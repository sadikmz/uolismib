#!/usr/bin/env python3

from collections import defaultdict
import argparse
import sys

class PAVprot:
    
    # Static method to convert FASTA to dict 
    def fasta2dict(source):
        """
        Generator: yields (header, sequence) from FASTA file or stdin.
        Uses 'with open' automatically when given a file path.
        """
        # If user passed '-', read from stdin
        if str(source) == '-':
            lines = sys.stdin
            close_at_end = False
        else:
            lines = open(source, 'r')
            close_at_end = True  # not needed with 'with', but kept for clarity

        # Use context manager only if we opened the file
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

                    header_line = line[1:].strip()
                    current_header = header_line
                    current_seq = []
                else:
                    current_seq.append(line)

            # Yield the last sequence
            if current_header:
                yield current_header, ''.join(current_seq)

    def parse_gffcompare_tracking(filepath: str, filter_codes: set = None):
        """
        Parse gffcompare .tracking → TSV table of matches (filtered or all)
        Grouped by reference gene (prot1)
        """

        full_dict = defaultdict(list)      # original unfiltered
        filtered_dict = defaultdict(list)  # only matching class codes

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

                # prot1 (reference)
                ref_gene, ref_trans = [x.strip() for x in ref_field.split('|')]
                ref_trans_clean = ref_trans.replace('rna-', '')

                # prot2 (query)
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

                # Always add to full dict
                full_dict[ref_gene].append(entry)

                # Add to filtered only if no filter or matches
                if not filter_codes or class_code in filter_codes:
                    filtered_dict[ref_gene].append(entry)

        return dict(full_dict), dict(filtered_dict)


def main():
    parser = argparse.ArgumentParser(
        description="FASTA → Python dict  {header: sequence}  – pure Python, safe & fast"
    )
    parser.add_argument('fasta_file', nargs='?', default='-', 
                        help="FASTA file or '-' to read from stdin (default: stdin)")
    parser.add_argument('--quiet', action='store_true',
                        help="Validate only – no output")
    parser.add_argument('--gff-comp', help="Path to the .tracking file")
    parser.add_argument(
        '--class-code',
        type=str,
        help="Comma-separated class codes to filter (e.g. em,j). Use 'em' for exact match"
    )
    parser.add_argument(
        '--tsv',
        action='store_true',
        help="Output as TSV (default behavior now)"
    )

    args = parser.parse_args()

    try:
        seq_dict = dict(PAVprot.fasta2dict(args.fasta_file))
        if not args.quiet:
            print(seq_dict)

    except Exception as e:
        print(f"Error reading FASTA: {e}", file=sys.stderr)
        sys.exit(1)
        
    filter_set = None
    if args.class_code:
        filter_set = {c.strip() for c in args.class_code.split(',') if c.strip()}

    full_rels, filtered_rels = PAVprot.parse_gffcompare_tracking(args.gff_comp, filter_set)

    # Use filtered if exists, otherwise full
    data_to_print = filtered_rels if filtered_rels else full_rels

    # Print TSV header
    print("ref_gene\tref_transcript\tquery_gene\tquery_transcript\tclass_code\texons")

    # Print rows
    for ref_gene, entries in data_to_print.items():
        for e in entries:
            print(f"{e['ref_gene']}\t{e['ref_transcript']}\t{e['query_gene']}\t{e['query_transcript']}\t{e['class_code']}\t{e['exons'] or '-'}")


if __name__ == '__main__':
    main()

# test = dict(fasta2dict("../test.fa"))
# print(test)