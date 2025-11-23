#!/usr/bin/env python3
"""
PAVprot
"""

from collections import defaultdict
import argparse
import sys
import os
import subprocess
import gzip

class PAVprot:
    @staticmethod
    def fasta2dict(source, is_query=False):
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
                line = line.rstrip('\n')
                if not line:
                    continue

                if line.startswith('>'):
                    if current_header:
                        yield current_header, ''.join(current_seq)

                    header = line[1:].strip()
                    transcript_id = header.split()[0].split('|')[0]

                    if is_query:
                        if len(transcript_id) >= 3 and transcript_id[-3] == '-' and transcript_id[-2] == 'p':
                            transcript_id = transcript_id[:-3]

                    current_header = transcript_id
                    current_seq = []
                else:
                    current_seq.append(line.upper())

            if current_header:
                yield current_header, ''.join(current_seq)

    @staticmethod
    def load_gff(gff_path: str):
        rna_to_protein = {}
        locus_to_gene = {}

        with open(gff_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '\tCDS\t' not in line:
                    continue
                attrs = line.split('\t')[8]
                attr_dict = {}
                for pair in attrs.split(';'):
                    if '=' in pair:
                        k, v = pair.split('=', 1)
                        attr_dict[k] = v

                parent = attr_dict.get('Parent', '')
                if parent.startswith('rna-'):
                    rna_id = parent[4:]
                    protein_id = attr_dict.get('GenBank') or attr_dict.get('protein_id')
                    if protein_id:
                        rna_to_protein[rna_id] = protein_id

                locus_tag = attr_dict.get('locus_tag', '')
                if locus_tag:
                    gene_id = f"gene-{locus_tag}"
                    locus_to_gene[locus_tag] = gene_id

        return rna_to_protein, locus_to_gene

    @classmethod
    def parse_tracking(cls, filepath: str, feature_table: str = None, filter_codes: set = None):
        rna_to_protein, locus_to_gene = {}, {}
        if feature_table:
            rna_to_protein, locus_to_gene = cls.load_gff(feature_table)

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

                ref_gene_raw, ref_trans_raw = [x.strip() for x in ref_field.split('|')]
                ref_trans_clean = ref_trans_raw.replace('rna-', '')
                ref_trans_final = rna_to_protein.get(ref_trans_clean, ref_trans_clean)
                ref_gene = locus_to_gene.get(ref_gene_raw, ref_gene_raw)

                q_gene_full = parts[0]
                q_gene = q_gene_full.split(':')[-1]
                q_trans = parts[1]
                try:
                    exons = int(parts[2])
                except ValueError:
                    exons = None

                entry = {
                    "ref_gene": ref_gene,
                    "ref_transcript": ref_trans_final,
                    "query_gene": q_gene,
                    "query_transcript": q_trans,
                    "class_code": class_code,
                    "exons": exons
                }

                full_dict[ref_gene].append(entry)
                if not filter_codes or class_code in filter_codes:
                    filtered_dict[ref_gene].append(entry)

        return dict(full_dict), dict(filtered_dict)


    @classmethod
    def filter_multi_transcripts(cls, full_dict: dict):
        
        """
        Assign class_type (for visualization purpose):
            0 → only em,c,k
            1 → only em,c,k,j
            2 → anything else
            3 → single-transcript query genes (no multi-transcript)
        """
        
        # Step 1: Group entries by query_gene
        query_gene_to_entries = defaultdict(list)
        for entries in full_dict.values():
            for entry in entries:
                query_gene_to_entries[entry['query_gene']].append(entry)
        
        # Step 2: Analyze each query_gene for multiple transcripts
        
        query_gene_info = {}
        
        for qgene, qentries in query_gene_to_entries.items():
            if len(qentries) <=1:
                # Only one transcript - no multi-transcript case
                class_codes = {qentries[0]['class_code']}
            else:
                # Multiple transcripts
                class_codes = {e['class_code'] for e in qentries}
            
            code_str = ';'.join(sorted(class_codes))
            
            # Assign class_type
            if class_codes <= {'em','c','k'}:
                ctype = '0'
            elif class_codes <= {'em','c','k','j'}:
                ctype = '1'
            else:
                ctype = '2'
            
            query_gene_info[qgene] = {'class_code_multi': code_str, 'class_type': ctype}
            
        # Step 3: Attach info back to entries
        for entries in full_dict.values():
            for entry in entries:
                qgene = entry['query_gene']
                # if qgene in query_gene_info:
                    # entry.update(query_gene_info[qgene])
                info = query_gene_info.get(qgene, {'class_code_multi': entry['class_code'], 'class_type': '3'})
                entry['class_code_multi'] = info['class_code_multi']
                entry['class_type'] = info['class_type']
                
        return full_dict 
    
class DiamondRunner:
    def __init__(self, threads: int = 40, output_prefix: str = "gffcompare"):
        self.threads = threads
        self.output_prefix = output_prefix

    def diamond_blastp(self, ref_faa_path: str, qry_faa_path: str) -> str:
        """Run one single all-vs-all DIAMOND blastp"""
        out_dir = os.path.join(os.getcwd(), 'pavprot_out', 'compareprot_out')
        os.makedirs(out_dir, exist_ok=True)
        diamond_out = os.path.join(out_dir, f"{self.output_prefix}_diamond_blastp.tsv.gz")
        
        
        cmd_str = (
            f"diamond blastp "
            f"--db {ref_faa_path} "
            f"--query {qry_faa_path} "
            f"--ultra-sensitive "
            f"--masking none "
            f"--out {diamond_out} "
            f"--outfmt 6 qseqid qlen sallseqid slen qstart qend sstart send evalue bitscore score length pident nident mismatch gapopen gaps qcovhsp scovhsp qstrand "
            f"--evalue 1e-6 "
            f"--threads {self.threads} "
            f"--max-hsps 1 "
            f"--unal 1 "
            f"--compress 1"
        )

        print(f"Running full DIAMOND blastp → {diamond_out}", file=sys.stderr)
        subprocess.run(cmd_str, shell=True, check=True)

        return diamond_out

    def enrich_blastp(self, data: dict, diamond_tsv_gz: str):
        """Parse DIAMOND output and enrich the dictionary"""
        hits = {}
        with gzip.open(diamond_tsv_gz, 'rt') as f:
            for line in f:
                if not line.strip():
                    continue
                parts = line.strip().split('\t')
                hit = {
                    "qseqid": parts[0], "qlen": int(parts[1]), "sallseqid": parts[2], "slen": int(parts[3]),
                    "qstart": int(parts[4]), "qend": int(parts[5]), "sstart": int(parts[6]), "send": int(parts[7]),
                    "evalue": float(parts[8]), "bitscore": float(parts[9]), "score": float(parts[10]),
                    "length": int(parts[11]), "pident": float(parts[12]), "nident": int(parts[13]),
                    "mismatch": int(parts[14]), "gapopen": int(parts[15]), "gaps": int(parts[16]),
                    "qcovhsp": float(parts[17]), "scovhsp": float(parts[18]), "qstrand": parts[19]
                }
                qid = hit["qseqid"]
                if qid not in hits or hit["bitscore"] > hits[qid]["bitscore"]:
                    hits[qid] = hit
        
        # add pidentCov_9090
        query_to_high_hits = defaultdict(list)
        
        for hit in hits.values():
            if hit["pident"] >= 90.0 and hit["qcovhsp"] >= 90.0:
                query_to_high_hits[hit["qseqid"]].append(hit['sallseqid'])
       
        # Only keep query transcripts with multiple high-quality hits
        multi_match_queries = {q for q, refs in query_to_high_hits.items() if len(refs) > 1} 

        for entries in data.values():
            for entry in entries:
                qid = entry["query_transcript"]
                if qid in hits:
                    h = hits[qid]
                    entry["diamond"] = h
                    entry['pident'] = h['pident']
                    entry['qcovhsp'] = h['qcovhsp']
                    entry["identical_aa"] = h["nident"]
                    entry["mismatched_aa"] = h["mismatch"]
                    entry["indels_aa"] = h["gaps"]
                    entry["aligned_aa"] = h["length"]
                else:
                    entry["diamond"] = None
                    entry["identical_aa"] = entry["mismatched_aa"] = entry["indels_aa"] = entry["aligned_aa"] = entry['pident'] = entry['qcovhsp'] = 0
                
                # add pidentCov_9090 info 
                if qid in multi_match_queries:
                    matching_refs = query_to_high_hits[qid]
                    entry['pidentCov_9090'] = {"ref_cnt": len(matching_refs), 
                                               "ref_trans": matching_refs}
                else:
                    entry['pidentCov_9090'] = None

        return data


def main():
    parser = argparse.ArgumentParser(description="PAVprot – complete class-based pipeline")
    parser.add_argument('--gff-comp', required=True)
    parser.add_argument('--ref-gff', help="GFF3 CDS feature table (optional)")
    parser.add_argument('--class-code', help="Comma-separated class codes (e.g. em,j)")
    parser.add_argument('--ref-faa', help="Reference proteins FASTA")
    parser.add_argument('--qry-faa', help="Query proteins FASTA")
    parser.add_argument('--run-diamond', action='store_true')
    parser.add_argument('--diamond-threads', type=int, default=40)
    parser.add_argument('--output-prefix', default="gffcompare")

    args = parser.parse_args()

    filter_set = {c.strip() for c in args.class_code.split(',')} if args.class_code else None
    full, filtered = PAVprot.parse_tracking(args.gff_comp, args.ref_gff, filter_set)
    data = filtered if filtered else full

    if args.run_diamond:
        if not args.ref_faa or not args.qry_faa:
            print("Error: --run-diamond requires --ref-faa and --qry-faa", file=sys.stderr)
            sys.exit(1)

        # Prepare input FASTA files
        pavprot_out = os.path.join(os.getcwd(), 'pavprot_out')
        compareprot_out = os.path.join(pavprot_out, 'compareprot_out')
        input_seq_dir = os.path.join(compareprot_out, 'input_seq_dir')
        os.makedirs(input_seq_dir, exist_ok=True)

        ref_faa_path = os.path.join(input_seq_dir, "ref_all.faa")
        qry_faa_path = os.path.join(input_seq_dir, "qry_all.faa")

        with open(ref_faa_path, 'w') as f:
            for h, s in PAVprot.fasta2dict(args.ref_faa, is_query=False):
                f.write(f">{h}\n{s}\n")
        with open(qry_faa_path, 'w') as f:
            for h, s in PAVprot.fasta2dict(args.qry_faa, is_query=True):
                f.write(f">{h}\n{s}\n")

        diamond = DiamondRunner(threads=args.diamond_threads, output_prefix=args.output_prefix)
        diamond_tsv_gz = diamond.diamond_blastp(ref_faa_path, qry_faa_path)
        data = diamond.enrich_blastp(data, diamond_tsv_gz)
        

    # Apply multi-transcript classification
    data = PAVprot.filter_multi_transcripts(data)
    
    # Output
    pavprot_out = os.path.join(os.getcwd(), 'pavprot_out')
    os.makedirs(pavprot_out, exist_ok=True)

    if args.class_code:
        safe_codes = "_".join(sorted(filter_set))
        suffix = "_diamond_blastp.tsv" if args.run_diamond else ".tsv"
        output_file = os.path.join(pavprot_out, f"{args.output_prefix}_{safe_codes}{suffix}")
    else:
        suffix = "_diamond_blastp.tsv" if args.run_diamond else ".tsv"
        output_file = os.path.join(pavprot_out, f"{args.output_prefix}{suffix}")

    header = "ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons"
    if args.run_diamond:
        header += "\tidentical_aa\tmismatched_aa\tindels_aa\taligned_aa"

    with open(output_file, 'w') as f:
        f.write(header + "\n")
        for entries in data.values():
            for e in entries:
                exons = e.get('exons') if e.get('exons') is not None else '-'
                base = f"{e['ref_gene']}\t{e['ref_transcript']}\t{e['query_gene']}\t{e['query_transcript']}\t{e['class_code']}\t{exons}"
                if args.run_diamond:
                    f.write(f"{base}\t{e.get('identical_aa', 0)}\t{e.get('mismatched_aa', 0)}\t"
                            f"{e.get('indels_aa', 0)}\t{e.get('aligned_aa', 0)}\n")
                else:
                    f.write(base + "\n")
    print(f"Results saved to {output_file}", file=sys.stderr)


if __name__ == '__main__':
    main()