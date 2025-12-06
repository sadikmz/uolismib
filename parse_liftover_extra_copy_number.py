#!/usr/bin/env python3
"""
Extract extra copy number genes from Liftover GFF3 file
Generates a table with original gene IDs and their duplicated genes/transcripts
"""

import argparse
import sys
import os
from collections import defaultdict


def fasta2dict(fasta_file):
    """
    Parse FASTA file and yield (header, sequence) tuples
    """
    with open(fasta_file, 'r') as f:
        current_header = None
        current_seq = []

        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue

            if line.startswith('>'):
                if current_header:
                    yield current_header, ''.join(current_seq)

                header = line[1:].strip()
                transcript_id = header.split()[0]

                current_header = transcript_id
                current_seq = []
            else:
                current_seq.append(line.upper())

        if current_header:
            yield current_header, ''.join(current_seq)


def parse_all_liftover_transcripts(gff_path):
    """
    Parse all transcripts from liftover GFF3 file (mRNA features)

    Returns: set of all transcript IDs from the liftover GFF3
    """
    transcript_ids = set()

    with open(gff_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '\tmRNA\t' not in line:
                continue

            cols = line.split('\t')
            if len(cols) < 9:
                continue

            attrs = cols[8]

            # Parse attributes to get ID
            for pair in attrs.split(';'):
                if '=' not in pair:
                    continue
                k, v = pair.split('=', 1)

                if k == 'ID':
                    # Extract transcript ID
                    transcript_id = v.split('.')[0]  # remove version if present
                    transcript_ids.add(transcript_id)
                    break

    return transcript_ids


def parse_extra_copy_numbers(gff_path):
    """
    Parse Liftover GFF3 (mRNA features) and extract extra_copy_number information

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


def parse_tracking(filepath, feature_table=None, filter_codes=None):
    """
    Parse gffcompare tracking file to extract class codes for query transcripts
    (Borrowed from pavprot.py)

    Returns: dict mapping query_transcript -> class_code
    """
    transcript_to_class = {}

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

            q_trans = parts[1]
            transcript_to_class[q_trans] = class_code

    return transcript_to_class


def get_original_transcript_id(duplicated_transcript_id):
    """
    Extract the original transcript ID from a duplicated transcript ID
    E.g., FOZG_18552-t1_1 -> FOZG_18552-t1
    """
    if '_' in duplicated_transcript_id:
        parts = duplicated_transcript_id.rsplit('_', 1)
        # Check if last part is a number (copy indicator)
        if parts[-1].isdigit():
            return parts[0]
    return duplicated_transcript_id


def write_fasta_sequences(liftover_gff, input_fasta, class_codes_map=None):
    """
    Write FASTA sequences for liftover and gffcompare results

    Liftover FASTA: All transcripts from liftover GFF3 file
    Gffcompare FASTA: Original transcripts + duplicated transcripts from tracking file

    For duplicated transcripts, sequences are taken from their original transcript IDs

    Args:
        liftover_gff: path to liftover GFF3 file
        input_fasta: path to input FASTA file (if None, no FASTA output)
        class_codes_map: optional dict mapping transcript -> class_code from gffcompare
    """
    if not input_fasta:
        return

    # Derive output basename from input_fasta
    output_basename = os.path.splitext(os.path.basename(input_fasta))[0]

    # Load input FASTA sequences into a dictionary
    print("Loading input FASTA sequences...", file=sys.stderr)
    seq_dict = {}
    for header, seq in fasta2dict(input_fasta):
        seq_dict[header] = seq
    print(f"Loaded {len(seq_dict)} sequences from input FASTA", file=sys.stderr)

    # Parse all transcripts from liftover GFF3
    print("Parsing liftover GFF3...", file=sys.stderr)
    liftover_transcripts = parse_all_liftover_transcripts(liftover_gff)
    print(f"Found {len(liftover_transcripts)} transcripts in liftover GFF3", file=sys.stderr)

    # Write liftover FASTA output
    liftover_output = f"{output_basename}_liftover.faa"
    with open(liftover_output, 'w') as f:
        written_count = 0
        missing_count = 0

        for transcript_id in sorted(liftover_transcripts):
            sequence = None

            # First try exact match
            if transcript_id in seq_dict:
                sequence = seq_dict[transcript_id]
            else:
                # Try to find original transcript ID (remove suffix like _1, _2)
                original_id = get_original_transcript_id(transcript_id)
                if original_id != transcript_id and original_id in seq_dict:
                    sequence = seq_dict[original_id]

            if sequence:
                f.write(f">{transcript_id}\n{sequence}\n")
                written_count += 1
            else:
                missing_count += 1

    print(f"Wrote {written_count} sequences to {liftover_output}", file=sys.stderr)
    if missing_count > 0:
        print(f"Warning: {missing_count} transcripts not found in input FASTA", file=sys.stderr)

    # Write gffcompare FASTA output if class_codes_map is provided
    if class_codes_map:
        # Collect transcripts for gffcompare output
        # Include all original transcripts + duplicated transcripts from tracking
        gffcompare_transcripts = set()

        # Get all duplicated transcripts from tracking
        duplicated_in_tracking = {t for t in class_codes_map.keys() if get_original_transcript_id(t) != t}

        # Add duplicated transcripts from tracking
        gffcompare_transcripts.update(duplicated_in_tracking)

        # Add original transcripts for each duplicated transcript
        for dup_transcript in duplicated_in_tracking:
            original_transcript = get_original_transcript_id(dup_transcript)
            gffcompare_transcripts.add(original_transcript)

        gffcompare_output = f"{output_basename}_gffcompare.faa"
        with open(gffcompare_output, 'w') as f:
            written_count = 0
            missing_count = 0

            for transcript_id in sorted(gffcompare_transcripts):
                sequence = None

                # First try exact match
                if transcript_id in seq_dict:
                    sequence = seq_dict[transcript_id]
                else:
                    # Try to find original transcript ID (remove suffix like _1, _2)
                    original_id = get_original_transcript_id(transcript_id)
                    if original_id != transcript_id and original_id in seq_dict:
                        sequence = seq_dict[original_id]

                if sequence:
                    f.write(f">{transcript_id}\n{sequence}\n")
                    written_count += 1
                else:
                    missing_count += 1

        print(f"Wrote {written_count} sequences to {gffcompare_output}", file=sys.stderr)
        if missing_count > 0:
            print(f"Warning: {missing_count} transcripts not found in input FASTA", file=sys.stderr)


def write_output(extra_copies, output_file=None, class_codes_map=None):
    """
    Write the extra copy number table to output

    Format (without gffcompare):
    original_gene_id    duplicated_genes_liftover    duplicated_transcripts_liftover    count_dup_genes

    Format (with gffcompare):
    original_gene_id    duplicated_genes_liftover    duplicated_transcripts_liftover    duplicated_transcripts_gffcomp    count_dup_genes    class_codes
    """
    # Update header based on whether class_codes are provided
    header = "original_gene_id\tduplicated_genes_liftover\tduplicated_transcripts_liftover"
    if class_codes_map:
        header += "\tduplicated_transcripts_gffcomp"
    header += "\tcount_dup_genes"
    if class_codes_map:
        header += "\tclass_codes"
    header += "\n"

    if output_file:
        f = open(output_file, 'w')
    else:
        f = sys.stdout

    try:
        f.write(header)

        # Sort by original gene ID for consistent output
        for original_gene_id in sorted(extra_copies.keys()):
            info = extra_copies[original_gene_id]
            duplicated_genes_liftover = ','.join(sorted(info['duplicated_genes']))

            # Keep transcripts in sorted order to maintain consistent mapping
            sorted_transcripts = sorted(info['duplicated_transcripts'])
            duplicated_transcripts_liftover = ','.join(sorted_transcripts)

            count_dup_genes = len(info['duplicated_genes'])

            # Build the output line
            line = f"{original_gene_id}\t{duplicated_genes_liftover}\t{duplicated_transcripts_liftover}"

            # Add duplicated_transcripts_gffcomp column only if class_codes_map is provided
            if class_codes_map:
                gffcomp_transcripts = [t for t in sorted_transcripts if t in class_codes_map]
                duplicated_transcripts_gffcomp = ','.join(gffcomp_transcripts) if gffcomp_transcripts else '-'
                line += f"\t{duplicated_transcripts_gffcomp}"

            line += f"\t{count_dup_genes}"

            # Add class codes if provided
            if class_codes_map:
                # Get class codes in the same order as sorted transcripts
                class_codes = []
                for transcript in sorted_transcripts:
                    class_code = class_codes_map.get(transcript, '-')
                    class_codes.append(class_code)
                line += f"\t{','.join(class_codes)}"

            f.write(line + "\n")

    finally:
        if output_file:
            f.close()


def main():
    parser = argparse.ArgumentParser(
        description="Extract extra copy number genes from liftover GFF3 file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --gff liftover.gff3
  %(prog)s --gff liftover.gff3 --output extra_copies.tsv
  %(prog)s --gff liftover.gff3 --gffcomp-tracking gffcompare.tracking --output extra_copies.tsv

Output format (without --gffcomp-tracking):
  Column 1: Original gene ID (e.g., FOZG_18552)
  Column 2: Comma-separated duplicated genes from liftover (e.g., FOZG_18552_1,FOZG_18552_2)
  Column 3: Comma-separated duplicated transcripts from liftover (e.g., FOZG_18552-t1_1,FOZG_18552-t1_2)
  Column 4: Count of duplicated genes (e.g., 2)

Output format (with --gffcomp-tracking):
  Column 1: Original gene ID (e.g., FOZG_18552)
  Column 2: Comma-separated duplicated genes from liftover (e.g., FOZG_18552_1,FOZG_18552_2)
  Column 3: Comma-separated duplicated transcripts from liftover (e.g., FOZG_18552-t1_1,FOZG_18552-t1_2)
  Column 4: Comma-separated duplicated transcripts found in gffcompare (e.g., FOZG_18552-t1_1)
  Column 5: Count of duplicated genes (e.g., 2)
  Column 6: Comma-separated class codes (e.g., em,j)
        """
    )

    parser.add_argument(
        '--gff',
        required=True,
        help='Input liftover GFF3 file'
    )
    parser.add_argument(
        '--gffcomp-tracking',
        help='Optional gffcompare tracking file to include class codes'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output TSV file (default: stdout)'
    )
    parser.add_argument(
        '--input-fasta',
        help='Optional input FASTA file to generate liftover and gffcompare FASTA outputs'
    )

    args = parser.parse_args()

    # Parse GFF file
    extra_copies = parse_extra_copy_numbers(args.gff)

    if not extra_copies:
        print("Warning: No extra copy number entries found in the GFF file", file=sys.stderr)
    else:
        print(f"Found {len(extra_copies)} original genes with extra copies", file=sys.stderr)

    # Parse gffcompare tracking file if provided
    class_codes_map = None
    if args.gffcomp_tracking:
        class_codes_map = parse_tracking(args.gffcomp_tracking)
        print(f"Parsed {len(class_codes_map)} transcript class codes from tracking file", file=sys.stderr)

    # Write output
    write_output(extra_copies, args.output, class_codes_map)

    if args.output:
        print(f"Output written to {args.output}", file=sys.stderr)

    # Write FASTA sequences if input FASTA is provided
    if args.input_fasta:
        write_fasta_sequences(args.gff, args.input_fasta, class_codes_map)


if __name__ == '__main__':
    main()
