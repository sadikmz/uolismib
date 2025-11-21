#!/usr/bin/env python3
"""
PAVprot pipeline
--run-diamond → optional: only runs DIAMOND if you explicitly ask for it
"""

from collections import defaultdict
import argparse
import sys
import os
import subprocess
import tempfile
import gzip

# =================================================================
# CLASS 1: PAVprot – FASTA + gffcompare tracking parser
# =================================================================
class PAVprot:
    @staticmethod
    def fasta2dict(source):
        if str(source) == '-':
            lines = sys.stdin
            close_at_end = False
        else:
            lines = open(source, 'r')
            close_at_end = True

        context = lines if not close_at_end else open(source, 'r')
        with context:
            current_header = None
            current_seq = []
            for line in context:
                line = line.strip()
                if not line:
                    continue
                if line.startswith('>'):
                    if current_header:
                        yield current_header, ''.join(current_seq)
                    current_header = line[1:].strip()
                    current_seq = []
                else:
                    current_seq.append(line.upper())
            if current_header:
                yield current_header, ''.join(current_seq)

    @staticmethod
    def parse_gffcompare_tracking(filepath: str, filter_codes: set = None):
        full_dict = defaultdict(list)
        filtered_dict = defaultdict(list)
        filter_codes = filter_codes or set()

        with open(filepath) as f:
            for line in f:
                line = line.rstrip('\n')
                if not line or line.startswith('#'):
                    continue

                fields = line.split('\t')
                if len(fields) < 5:
                    continue

                ref_field = fields[2].strip()
                if ref_field == '-' or '|' not in ref_field:
                    continue

                class_code = fields[3].strip()
                if class_code == '=':
                    class_code = 'em'

                query_info = fields[4].strip()
                parts = query_info.split('|')
                if len(parts) < 3:
                    continue

                ref_gene, ref_trans = [x.strip() for x in ref_field.split('|')]
                ref_trans_clean = ref_trans.replace('rna-', '')

                q_gene_full = parts[0]
                q_gene = q_gene_full.split(':')[-1]
                q_trans = parts[1]
                try:
                    exons = int(parts[2])
                except ValueError:
                    exons = None

                entry = {
                    "ref_gene": ref_gene,
                    "ref_transcript": ref_trans_clean,
                    "query_gene": q_gene,
                    "query_transcript": q_trans,
                    "class_code": class_code,
                    "exons": exons
                }

                full_dict[ref_gene].append(entry)
                if not filter_codes or class_code in filter_codes:
                    filtered_dict[ref_gene].append(entry)

        return dict(full_dict), dict(filtered_dict)


# =================================================================
# CLASS 2: CompareProt – optional DIAMOND alignment
# =================================================================
class CompareProt:
    def __init__(self, diamond_path: str = "diamond", threads: int = 48):
        self.diamond = diamond_path
        self.threads = threads
        self.tmpdir = tempfile.TemporaryDirectory()

    def _write_fasta(self, seqs: dict, path: str):
        with open(path, 'w') as f:
            for h, s in seqs.items():
                f.write(f">{h}\n{s}\n")

    def _run_diamond(self, db_faa: str, qry_faa: str, prefix: str) -> str:
        out = os.path.join(self.tmpdir.name, f"{prefix}.tsv.gz")
        cmd = [
            self.diamond, "blastp",
            "--db", db_faa, "--query", qry_faa,
            "--ultra-sensitive", "--masking", "none",
            "--out", out,
            "--outfmt", "6 qseqid qlen sallseqid slen qstart qend sstart send evalue bitscore score length pident nident mismatch gapopen gaps qcovhsp scovhsp qstrand",
            "--evalue", "1e-6", "--threads", str(self.threads),
            "--max-hsps", "10", "--unal", "1", "--compress", "1"
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out

    def _parse_diamond(self, tsv_gz: str):
        hits = {}
        with gzip.open(tsv_gz, 'rt') as f:
            for line in f:
                if not line.strip():
                    continue
                f = line.strip().split('\t')
                hit = {
                    "qseqid": f[0], "qlen": int(f[1]), "sallseqid": f[2], "slen": int(f[3]),
                    "qstart": int(f[4]), "qend": int(f[5]), "sstart": int(f[6]), "send": int(f[7]),
                    "evalue": float(f[8]), "bitscore": float(f[9]), "score": float(f[10]),
                    "length": int(f[11]), "pident": float(f[12]), "nident": int(f[13]),
                    "mismatch": int(f[14]), "gapopen": int(f[15]), "gaps": int(f[16]),
                    "qcovh            ": float(f[17]), "scovhsp": float(f[18]), "qstrand": f[19]
                }
                qid = hit["qseqid"]
                if qid not in hits or hit["bitscore"] > hits[qid]["bitscore"]:
                    hits[qid] = hit
        return hits

    def enrich(self, full_dict: dict, ref_faa_dict: dict, qry_faa_dict: dict):
        ref_faa = os.path.join(self.tmpdir.name, "ref.faa")
        self._write_fasta(ref_faa_dict, ref_faa)
        subprocess.run([self.diamond, "makedb", "--in", ref_faa, "--db", ref_faa],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for ref_gene, entries in full_dict.items():
            qry_seqs = {e["query_transcript"]: qry_faa_dict.get(e["query_transcript"], "")
                        for e in entries if e["query_transcript"] in qry_faa_dict}
            if not qry_seqs:
                continue

            qry_faa = os.path.join(self.tmpdir.name, f"qry_{ref_gene}.faa")
            self._write_fasta(qry_seqs, qry_faa)

            diamond_out = self._run_diamond(ref_faa, qry_faa, ref_gene)
            hits = self._parse_diamond(diamond_out)

            for entry in entries:
                qid = entry["query_transcript"]
                if qid in hits:
                    h = hits[qid]
                    entry["diamond"] = h
                    entry["identical_aa"] = h["nident"]
                    entry["mismatched_aa"] = h["mismatch"]
                    entry["indels_aa"] = h["gaps"]
                    entry["aligned_aa"] = h["length"]
                else:
                    entry["diamond"] = None
                    entry["identical_aa"] = entry["mismatched_aa"] = entry["indels_aa"] = entry["aligned_aa"] = 0

        return full_dict

    def __del__(self):
        try:
            self.tmpdir.cleanup()
        except:
            pass


# =================================================================
# main() – DIAMOND is now OPT-IN with --run-diamond
# =================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PAVprot pipeline")
    parser.add_argument('--gff-comp', required=True, help="gffcompare .tracking file")
    parser.add_argument('--class-code', help="Comma-separated class codes (e.g. em,j)")
    parser.add_argument('--ref-faa', help="Reference proteins FASTA")
    parser.add_argument('--qry-faa', help="Query proteins FASTA")
    parser.add_argument('--run-diamond', action='store_true', 
                        help="Run DIAMOND blastp and enrich results (optional, off by default)")

    args = parser.parse_args()

    filter_set = {c.strip() for c in args.class_code.split(',')} if args.class_code else None
    full, filtered = PAVprot.parse_gffcompare_tracking(args.gff_comp, filter_set)
    data = filtered if filtered else full

    # DIAMOND only if explicitly requested
    if args.run_diamond:
        if not args.ref_faa or not args.qry_faa:
            print("Error: --run-diamond requires --ref-faa and --qry-faa", file=sys.stderr)
            sys.exit(1)
        ref_seqs = dict(PAVprot.fasta2dict(args.ref_faa))
        qry_seqs = dict(PAVprot.fasta2dict(args.qry_faa))
        comparer = CompareProt(threads=48)
        data = comparer.enrich(data, ref_seqs, qry_seqs)

    # Default TSV output
    print("ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons"
          "\tidentical_aa\tmismatched_aa\tindels_aa\taligned_aa" if args.run_diamond else "")
    for ref_gene, entries in data.items():
        for e in entries:
            base = f"{e['ref_gene']}\t{e['ref_transcript']}\t{e['query_gene']}\t{e['query_transcript']}\t{e['class_code']}\t{e.get('exons', '-')}"
            if args.run_diamond:
                print(f"{base}\t{e.get('identical_aa', 0)}\t{e.get('mismatched_aa', 0)}\t"
                      f"{e.get('indels_aa', 0)}\t{e.get('aligned_aa', 0)}")
            else:
                print(base)