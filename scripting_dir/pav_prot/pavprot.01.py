#!/usr/bin/env python3
"""
PAVprot: Combined tool
- FASTA → dict (optional)
- gffcompare .tracking → TSV (default output)
  • If --class-code given → save to filtered_<codes>.txt
  • Otherwise → print to stdout
"""

from collections import defaultdict
import argparse
import sys
import os

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


def main():
    parser = argparse.ArgumentParser(description="PAVprot: FASTA dict + gffcompare tracking → TSV")
    parser.add_argument('fasta_file', nargs='?', default=None, help="FASTA file (optional)")
    parser.add_argument('--gff-comp', help="Path to gffcompare .tracking file")
    parser.add_argument('--class-code', type=str, help="Comma-separated class codes (e.g. em,j,u)")
    parser.add_argument('--quiet', action='store_true', help="Suppress FASTA dict output")

    args = parser.parse_args()

    # FASTA part (optional)
    if args.fasta_file:
        try:
            seq_dict = dict(PAVprot.fasta2dict(args.fasta_file))
            if not args.quiet:
                print(seq_dict)
        except Exception as e:
            print(f"Error reading FASTA: {e}", file=sys.stderr)
            sys.exit(1)

    # Tracking part
    if args.gff_comp:
        filter_set = None
        output_file = None

        if args.class_code:
            codes = [c.strip() for c in args.class_code.split(',') if c.strip()]
            filter_set = set(codes)
            safe_codes = "_".join(sorted(codes))
            output_file = f"filtered_{safe_codes}.txt"

        full_rels, filtered_rels = PAVprot.parse_gffcompare_tracking(args.gff_comp, filter_set)
        data_to_print = filtered_rels if filtered_rels else full_rels

        # Decide where to write
        if output_file:
            with open(output_file, 'w') as out_f:
                out_f.write("ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons\n")
                for ref_gene, entries in data_to_print.items():
                    for e in entries:
                        exons_val = e['exons'] if e['exons'] is not None else '-'
                        out_f.write(f"{e['ref_gene']}\t{e['ref_transcript']}\t"
                                    f"{e['query_gene']}\t{e['query_transcript']}\t"
                                    f"{e['class_code']}\t{exons_val}\n")
            print(f"Filtered results saved to: {output_file}", file=sys.stderr)
        else:
            # Print to stdout
            print("ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons")
            for ref_gene, entries in data_to_print.items():
                for e in entries:
                    exons_val = e['exons'] if e['exons'] is not None else '-'
                    print(f"{e['ref_gene']}\t{e['ref_transcript']}\t"
                          f"{e['query_gene']}\t{e['query_transcript']}\t"
                          f"{e['class_code']}\t{exons_val}")


if __name__ == '__main__':
    main()