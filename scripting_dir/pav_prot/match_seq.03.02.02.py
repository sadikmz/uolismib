#!/usr/bin/env python3
import os
import subprocess
import tempfile
from collections import defaultdict
from typing import Dict, List, Any

class CompareProt:
    """
    Run DIAMOND blastp between reference and query protein pairs from full_dict
    and enrich each entry with alignment statistics.
    """

    def __init__(self, diamond_path: str = "diamond", threads: int = 48):
        self.diamond = diamond_path
        self.threads = threads
        self.tmp_dir = tempfile.TemporaryDirectory()

    def _write_fasta(self, seq_dict: Dict[str, str], fasta_path: str):
        """Write dict of sequences to FASTA file"""
        with open(fasta_path, 'w') as f:
            for header, seq in seq_dict.items():
                f.write(f">{header}\n{seq}\n")

    def _run_diamond(self, ref_faa: str, qry_faa: str, prefix: str) -> str:
        """Run DIAMOND blastp with your exact settings"""
        out_file = os.path.join(self.tmp_dir.name, f"{prefix}.tsv.gz")

        cmd = [
            self.diamond, "blastp",
            "--db", ref_faa,
            "--query", qry_faa,
            "--ultra-sensitive",
            "--masking", "none",
            "--out", out_file,
            "--outfmt", "6 qseqid qlen sallseqid slen qstart qend sstart send evalue bitscore score length pident nident mismatch gapopen gaps qcovhsp scovhsp qstrand",
            "--evalue", "1e-6",
            "--threads", str(self.threads),
            "--max-hsps", "10",
            "--unal", "1",
            "--compress", "1"
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_file

    def _parse_diamond_tsv(self, tsv_gz: str) -> List[Dict[str, Any]]:
        """Parse compressed DIAMOND TSV and return list of best hits per query"""
        import gzip

        hits = []
        with gzip.open(tsv_gz, 'rt') as f:
            for line in f:
                if not line.strip() or line.startswith('#'):
                    continue
                fields = line.strip().split('\t')
                hit = {
                    "qseqid": fields[0],
                    "qlen": int(fields[1]),
                    "sallseqid": fields[2],
                    "slen": int(fields[3]),
                    "qstart": int(fields[4]),
                    "qend": int(fields[5]),
                    "sstart": int(fields[6]),
                    "send": int(fields[7]),
                    "evalue": float(fields[8]),
                    "bitscore": float(fields[9]),
                    "score": float(fields[10]),
                    "length": int(fields[11]),      # alignment length
                    "pident": float(fields[12]),
                    "nident": int(fields[13]),      # number of identical AA
                    "mismatch": int(fields[14]),
                    "gapopen": int(fields[15]),
                    "gaps": int(fields[16]),        # total gaps (insertions + deletions)
                    "qcovhsp": float(fields[17]),
                    "scovhsp": float(fields[18]),
                    "qstrand": fields[19]
                }
                hits.append(hit)
        return hits

    def enrich_with_alignment(self, full_dict: Dict[str, List[dict]], ref_faa_dict: Dict[str, str], qry_faa_dict: Dict[str, str]):
        """
        Main method: runs DIAMOND on all pairs in full_dict and appends results.
        Modifies full_dict in-place.
        """
        # Build temporary DB from reference proteins in this comparison
        ref_faa_path = os.path.join(self.tmp_dir.name, "ref_prot.faa")
        self._write_fasta(ref_faa_dict, ref_faa_path)

        # Make DIAMOND DB
        subprocess.run([self.diamond, "makedb", "--in", ref_faa_path, "--db", ref_faa_path], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Process each reference gene group
        for ref_gene, entries in full_dict.items():
            # Extract query sequences for this ref_gene group
            qry_seqs = {}
            for e in entries:
                qry_trans = e["query_transcript"]
                if qry_trans in qry_faa_dict:
                    qry_seqs[qry_trans] = qry_faa_dict[qry_trans]

            if not qry_seqs:
                continue

            qry_faa_path = os.path.join(self.tmp_dir.name, f"qry_{ref_gene}.faa")
            self._write_fasta(qry_seqs, qry_faa_path)

            # Run DIAMOND
            diamond_out = self._run_diamond(ref_faa_path, qry_faa_path, f"{ref_gene}")

            # Parse results
            alignments = self._parse_diamond_tsv(diamond_out)

            # Match back to entries (best hit per query transcript)
            alignment_map = {}
            for hit in alignments:
                qid = hit["qseqid"]
                if qid not in alignment_map or hit["bitscore"] > alignment_map[qid]["bitscore"]:
                    # Add summary stats
                    hit["identical_aa"] = hit["nident"]
                    hit["mismatched_aa"] = hit["mismatch"]
                    hit["indels_aa"] = hit["gaps"]  # insertions + deletions
                    hit["aligned_aa"] = hit["length"]
                    alignment_map[qid] = hit

            # Append to original entries
            for entry in entries:
                qry_trans = entry["query_transcript"]
                if qry_trans in alignment_map:
                    diamond_hit = alignment_map[qry_trans]
                    entry["diamond"] = diamond_hit  # full DIAMOND fields
                    entry["identical_aa"] = diamond_hit["identical_aa"]
                    entry["mismatched_aa"] = diamond_hit["mismatched_aa"]
                    entry["indels_aa"] = diamond_hit["indels_aa"]
                    entry["aligned_aa"] = diamond_hit["aligned_aa"]
                else:
                    # No alignment found
                    entry["diamond"] = None
                    entry["identical_aa"] = entry["mismatched_aa"] = entry["indels_aa"] = entry["aligned_aa"] = 0

        return full_dict

    def __del__(self):
        self.tmp_dir.cleanup()
    
    
    