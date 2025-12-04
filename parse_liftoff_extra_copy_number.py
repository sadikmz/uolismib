#!/usr/bin/env python3
"""
Extract extra copy number genes from Liftoff GFF3 file
Generates a table with original gene IDs and their duplicated genes/transcripts
"""

import argparse
import sys
from collections import defaultdict


def parse_extra_copy_numbers(gff_path):
    """
    Parse Liftoff GFF3 (mRNA features) and extract extra_copy_number information

    Returns: dict mapping original_gene_id -> {
        'duplicated_genes': set of gene IDs,
        'duplicated_transcripts': set of transcript IDs
    }
    """
    extra_copies = defaultdict(lambda: {'duplicated_genes': set(), 'duplicated_transcripts': set()})

    with open(gff_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '\tmRNA\t' not in line:
                continue

            cols = line.split('\t')
            if len(cols) < 9:
                continue

            attrs = cols[8]
            transcript_id = None
            parent_id = None
            copy_number = None

            # Parse attributes
            for pair in attrs.split(';'):
                if '=' not in pair:
                    continue
                k, v = pair.split('=', 1)

                if k == 'ID':
                    # Extract transcript ID (e.g. from "ID=FOZG_02018-t36_1")
                    transcript_id = v.split('.')[0]  # remove version if present
                elif k == 'Parent':
                    # Extract parent gene ID (e.g. from "Parent=FOZG_18552_1")
                    parent_id = v.split('.')[0]  # remove version if present
                elif k.lower() == 'extra_copy_number':
                    try:
                        copy_number = int(v)
                    except ValueError:
                        copy_number = None

            # Only process entries with extra_copy_number > 0
            if copy_number and copy_number > 0 and parent_id and transcript_id:
                # Extract original gene ID by removing the suffix (e.g., FOZG_18552_1 -> FOZG_18552)
                # The suffix pattern is typically _<number>
                if '_' in parent_id:
                    parts = parent_id.rsplit('_', 1)
                    # Check if last part is a number (copy indicator)
                    if parts[-1].isdigit():
                        original_gene_id = parts[0]
                    else:
                        # If not a digit, use the whole parent_id as original
                        original_gene_id = parent_id
                else:
                    original_gene_id = parent_id

                # Add the duplicated gene and transcript
                extra_copies[original_gene_id]['duplicated_genes'].add(parent_id)
                extra_copies[original_gene_id]['duplicated_transcripts'].add(transcript_id)

    return extra_copies


def write_output(extra_copies, output_file=None):
    """
    Write the extra copy number table to output

    Format:
    original_gene_id    duplicated_genes    duplicated_transcripts    count_dup_genes
    """
    header = "original_gene_id\tduplicated_genes\tduplicated_transcripts\tcount_dup_genes\n"

    if output_file:
        f = open(output_file, 'w')
    else:
        f = sys.stdout

    try:
        f.write(header)

        # Sort by original gene ID for consistent output
        for original_gene_id in sorted(extra_copies.keys()):
            info = extra_copies[original_gene_id]
            duplicated_genes = ','.join(sorted(info['duplicated_genes']))
            duplicated_transcripts = ','.join(sorted(info['duplicated_transcripts']))
            count_dup_genes = len(info['duplicated_genes'])

            f.write(f"{original_gene_id}\t{duplicated_genes}\t{duplicated_transcripts}\t{count_dup_genes}\n")

    finally:
        if output_file:
            f.close()


def main():
    parser = argparse.ArgumentParser(
        description="Extract extra copy number genes from Liftoff GFF3 file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --gff liftoff.gff3
  %(prog)s --gff liftoff.gff3 --output extra_copies.tsv

Output format:
  Column 1: Original gene ID (e.g., FOZG_18552)
  Column 2: Comma-separated duplicated genes (e.g., FOZG_18552_1,FOZG_18552_2)
  Column 3: Comma-separated duplicated transcripts (e.g., FOZG_18552-t1_1,FOZG_18552-t1_2)
  Column 4: Count of duplicated genes (e.g., 2)
        """
    )

    parser.add_argument(
        '--gff',
        required=True,
        help='Input Liftoff GFF3 file'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output TSV file (default: stdout)'
    )

    args = parser.parse_args()

    # Parse GFF file
    extra_copies = parse_extra_copy_numbers(args.gff)

    if not extra_copies:
        print("Warning: No extra copy number entries found in the GFF file", file=sys.stderr)
    else:
        print(f"Found {len(extra_copies)} original genes with extra copies", file=sys.stderr)

    # Write output
    write_output(extra_copies, args.output)

    if args.output:
        print(f"Output written to {args.output}", file=sys.stderr)


if __name__ == '__main__':
    main()
