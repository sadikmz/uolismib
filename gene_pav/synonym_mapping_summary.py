#!/usr/bin/env python3
"""
Generate summary statistics for synonym_mapping_liftover_gffcomp.tsv files.

Usage:
    python synonym_mapping_summary.py <input_file>
    python synonym_mapping_summary.py synonym_mapping_liftover_gffcomp.tsv
"""

import sys
import argparse
import pandas as pd


def generate_summary_statistics(input_file):
    """Generate summary statistics for synonym_mapping_liftover_gffcomp.tsv"""

    # Read the TSV file
    df = pd.read_csv(input_file, sep='\t')

    print("=" * 80)
    print("SUMMARY STATISTICS FOR SYNONYM_MAPPING_LIFTOVER_GFFCOMP")
    print("=" * 80)

    # Basic counts
    print(f"\n## BASIC COUNTS")
    print(f"Total records: {len(df)}")
    print(f"Unique reference genes: {df['ref_gene'].nunique()}")
    print(f"Unique reference transcripts: {df['ref_transcript'].nunique()}")
    print(f"Unique query genes: {df['query_gene'].nunique()}")
    print(f"Unique query transcripts: {df['query_transcript'].nunique()}")

    # Class code distribution
    print(f"\n## CLASS CODE DISTRIBUTION")
    class_code_counts = df['class_code'].value_counts().sort_index()
    print(class_code_counts.to_string())

    # Class type distribution
    print(f"\n## CLASS TYPE DISTRIBUTION")
    class_type_counts = df['class_type'].value_counts().sort_index()
    print(class_type_counts.to_string())

    # Exon distribution
    print(f"\n## EXON COUNT DISTRIBUTION")
    exon_stats = df['exons'].describe()
    print(exon_stats.to_string())
    print(f"\nExon count frequency:")
    exon_counts = df['exons'].value_counts().sort_index()
    print(exon_counts.head(20).to_string())

    # emckmnj and emckmnje distribution
    print(f"\n## EMCKMNJ DISTRIBUTION")
    emckmnj_counts = df['emckmnj'].value_counts().sort_index()
    print(emckmnj_counts.to_string())

    print(f"\n## EMCKMNJE DISTRIBUTION")
    emckmnje_counts = df['emckmnje'].value_counts().sort_index()
    print(emckmnje_counts.to_string())

    # Query genes per reference gene
    print(f"\n## QUERY GENES PER REFERENCE GENE")
    qry_per_ref = df.groupby('ref_gene')['query_gene'].nunique()
    print(f"Min query genes per ref gene: {qry_per_ref.min()}")
    print(f"Max query genes per ref gene: {qry_per_ref.max()}")
    print(f"Average query genes per ref gene: {qry_per_ref.mean():.2f}")
    print(f"Median query genes per ref gene: {qry_per_ref.median():.2f}")

    print(f"\nDistribution of query gene counts:")
    qry_distribution = qry_per_ref.value_counts().sort_index()
    print(qry_distribution.head(20).to_string())

    # Reference genes per query gene
    print(f"\n## REFERENCE GENES PER QUERY GENE")
    ref_per_qry = df.groupby('query_gene')['ref_gene'].nunique()
    print(f"Min reference genes per query gene: {ref_per_qry.min()}")
    print(f"Max reference genes per query gene: {ref_per_qry.max()}")
    print(f"Average reference genes per query gene: {ref_per_qry.mean():.2f}")
    print(f"Median reference genes per query gene: {ref_per_qry.median():.2f}")

    print(f"\nDistribution of reference gene counts:")
    ref_distribution = ref_per_qry.value_counts().sort_index()
    print(ref_distribution.head(20).to_string())

    print("\n" + "=" * 80)

def main():
    parser = argparse.ArgumentParser(
        description='Generate summary statistics for synonym_mapping_liftover_gffcomp.tsv files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python synonym_mapping_summary.py synonym_mapping_liftover_gffcomp.tsv
  python synonym_mapping_summary.py output/mapping_results.tsv
        '''
    )
    parser.add_argument(
        'input_file',
        help='Path to synonym_mapping_liftover_gffcomp.tsv file'
    )

    args = parser.parse_args()
    generate_summary_statistics(args.input_file)


if __name__ == '__main__':
    main()
