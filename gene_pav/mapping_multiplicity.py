#!/usr/bin/env python3
"""
Detect multiple mapping genes in synonym_mapping_liftover_gffcomp.tsv
- One ref gene to multiple query genes (1-to-many)
- One query gene to multiple ref genes (many-to-1)
"""

import sys
import argparse
import pandas as pd
from pathlib import Path

def detect_multiple_mappings(input_file, output_prefix=None):
    """
    Detect genes with multiple mappings.

    Args:
        input_file: Path to synonym_mapping_liftover_gffcomp.tsv
        output_prefix: Prefix for output files (default: input filename without extension)
    """
    # Read the TSV file
    print(f"Reading {input_file}...")
    df = pd.read_csv(input_file, sep='\t')

    # Set output directory (same as input file) and prefix
    input_path = Path(input_file)
    output_dir = input_path.parent

    if output_prefix is None:
        output_prefix = input_path.stem

    # Ensure output files are in the same directory as input
    output_prefix = str(output_dir / output_prefix)

    # ========================================================================
    # 1. Detect ref genes mapping to multiple query genes (1-to-many)
    # ========================================================================
    print("\nAnalyzing ref genes mapping to multiple query genes...")
    ref_to_qry = df.groupby('old_gene').agg({
        'new_gene': lambda x: list(x.unique()),
        'old_transcript': lambda x: list(x.unique()),
        'new_transcript': 'count',
        'class_code': lambda x: ';'.join(sorted(set(x)))
    }).reset_index()

    # Add count of unique query genes
    ref_to_qry['num_new_genes'] = ref_to_qry['new_gene'].apply(len)
    ref_to_qry['num_old_transcripts'] = ref_to_qry['old_transcript'].apply(len)

    # Filter for multiple mappings
    ref_multi = ref_to_qry[ref_to_qry['num_new_genes'] > 1].copy()
    ref_multi = ref_multi.sort_values('num_new_genes', ascending=False)

    # Format new_gene list as string
    ref_multi['new_genes_list'] = ref_multi['new_gene'].apply(lambda x: ';'.join(x))
    ref_multi['old_transcripts_list'] = ref_multi['old_transcript'].apply(lambda x: ';'.join(x))

    # Select and rename columns for output
    ref_output = ref_multi[[
        'old_gene',
        'num_old_transcripts',
        'num_new_genes',
        'new_genes_list',
        'old_transcripts_list',
        'new_transcript',
        'class_code'
    ]].rename(columns={
        'new_transcript': 'num_mappings',
        'class_code': 'class_codes'
    })

    # Save summary to file
    ref_output_file = f"{output_prefix}_ref_to_multiple_query.tsv"
    ref_output.to_csv(ref_output_file, sep='\t', index=False)
    print(f"✓ Found {len(ref_output)} ref genes mapping to multiple query genes")
    print(f"  Output: {ref_output_file}")

    # Create detailed output with one row per mapping
    print("  Generating detailed output...")
    ref_multi_genes = set(ref_multi['old_gene'])
    ref_detailed = df[df['old_gene'].isin(ref_multi_genes)].copy()
    ref_detailed = ref_detailed.sort_values(['old_gene', 'new_gene', 'old_transcript', 'new_transcript'])

    # Select relevant columns for detailed output (use all available columns from input)
    ref_detailed_output = ref_detailed.copy()

    ref_detailed_file = f"{output_prefix}_ref_to_multiple_query_detailed.tsv"
    ref_detailed_output.to_csv(ref_detailed_file, sep='\t', index=False)
    print(f"  Detailed output: {ref_detailed_file} ({len(ref_detailed_output)} mappings)")

    # ========================================================================
    # 2. Detect query genes mapping to multiple ref genes (many-to-1)
    # ========================================================================
    print("\nAnalyzing query genes mapping to multiple ref genes...")
    qry_to_ref = df.groupby('new_gene').agg({
        'old_gene': lambda x: list(x.unique()),
        'new_transcript': lambda x: list(x.unique()),
        'old_transcript': 'count',
        'class_code': lambda x: ';'.join(sorted(set(x)))
    }).reset_index()

    # Add count of unique ref genes
    qry_to_ref['num_old_genes'] = qry_to_ref['old_gene'].apply(len)
    qry_to_ref['num_new_transcripts'] = qry_to_ref['new_transcript'].apply(len)

    # Filter for multiple mappings
    qry_multi = qry_to_ref[qry_to_ref['num_old_genes'] > 1].copy()
    qry_multi = qry_multi.sort_values('num_old_genes', ascending=False)

    # Format old_gene list as string
    qry_multi['old_genes_list'] = qry_multi['old_gene'].apply(lambda x: ';'.join(x))
    qry_multi['new_transcripts_list'] = qry_multi['new_transcript'].apply(lambda x: ';'.join(x))

    # Select and rename columns for output
    qry_output = qry_multi[[
        'new_gene',
        'num_new_transcripts',
        'num_old_genes',
        'old_genes_list',
        'new_transcripts_list',
        'old_transcript',
        'class_code'
    ]].rename(columns={
        'old_transcript': 'num_mappings',
        'class_code': 'class_codes'
    })

    # Save summary to file
    qry_output_file = f"{output_prefix}_query_to_multiple_ref.tsv"
    qry_output.to_csv(qry_output_file, sep='\t', index=False)
    print(f"✓ Found {len(qry_output)} query genes mapping to multiple ref genes")
    print(f"  Output: {qry_output_file}")

    # Create detailed output with one row per mapping
    print("  Generating detailed output...")
    qry_multi_genes = set(qry_multi['new_gene'])
    qry_detailed = df[df['new_gene'].isin(qry_multi_genes)].copy()
    qry_detailed = qry_detailed.sort_values(['new_gene', 'old_gene', 'new_transcript', 'old_transcript'])

    # Select relevant columns for detailed output (use all available columns from input)
    qry_detailed_output = qry_detailed.copy()

    qry_detailed_file = f"{output_prefix}_query_to_multiple_ref_detailed.tsv"
    qry_detailed_output.to_csv(qry_detailed_file, sep='\t', index=False)
    print(f"  Detailed output: {qry_detailed_file} ({len(qry_detailed_output)} mappings)")

    # ========================================================================
    # 3. Create combined summary
    # ========================================================================
    print("\nGenerating summary statistics...")
    summary_file = f"{output_prefix}_multiple_mappings_summary.txt"

    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("MULTIPLE MAPPINGS DETECTION SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Input file: {input_file}\n")
        f.write(f"Total mappings: {len(df)}\n")
        f.write(f"Unique ref genes: {df['old_gene'].nunique()}\n")
        f.write(f"Unique query genes: {df['new_gene'].nunique()}\n\n")

        f.write("=" * 80 + "\n")
        f.write("REF GENES MAPPING TO MULTIPLE QUERY GENES (1-to-many)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total ref genes with multiple mappings: {len(ref_output)}\n")
        if len(ref_output) > 0:
            f.write(f"Max query genes per ref: {ref_output['num_new_genes'].max()}\n")
            f.write(f"Average query genes per ref: {ref_output['num_new_genes'].mean():.2f}\n\n")

            f.write("Top 10 ref genes by number of query genes:\n")
            top_ref = ref_output.nlargest(10, 'num_new_genes')
            for _, row in top_ref.iterrows():
                f.write(f"  {row['old_gene']}: {row['num_new_genes']} query genes\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("QUERY GENES MAPPING TO MULTIPLE REF GENES (many-to-1)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total query genes with multiple mappings: {len(qry_output)}\n")
        if len(qry_output) > 0:
            f.write(f"Max ref genes per query: {qry_output['num_old_genes'].max()}\n")
            f.write(f"Average ref genes per query: {qry_output['num_old_genes'].mean():.2f}\n\n")

            f.write("Top 10 query genes by number of ref genes:\n")
            top_qry = qry_output.nlargest(10, 'num_old_genes')
            for _, row in top_qry.iterrows():
                f.write(f"  {row['new_gene']}: {row['num_old_genes']} ref genes\n")

        f.write("\n" + "=" * 80 + "\n")

    print(f"✓ Summary saved to: {summary_file}")

    print("\n" + "=" * 80)
    print("DETECTION COMPLETE")
    print("=" * 80)
    print(f"\nOutput files:")
    print(f"  1. {ref_output_file} (summary)")
    print(f"  2. {ref_detailed_file} (detailed)")
    print(f"  3. {qry_output_file} (summary)")
    print(f"  4. {qry_detailed_file} (detailed)")
    print(f"  5. {summary_file}")

    return ref_output, qry_output

def main():
    parser = argparse.ArgumentParser(
        description='Detect multiple mapping genes (1-to-many and many-to-1 relationships)')
    parser.add_argument('input_file',
                        help='Path to synonym_mapping_liftover_gffcomp.tsv')
    parser.add_argument('--output-prefix', '-o',
                        help='Prefix for output files (default: input filename)')

    args = parser.parse_args()
    detect_multiple_mappings(args.input_file, args.output_prefix)

if __name__ == '__main__':
    main()
