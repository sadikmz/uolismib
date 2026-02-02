#!/usr/bin/env python3
"""
Synonym Mapping Parser for PAVprot Pipeline

This script parses synonym mapping files and extracts relevant information
for gene annotation comparison analysis.
"""

import sys
import pandas as pd
import argparse
from pathlib import Path
from typing import List, Optional


# Default column names - can be overridden via CLI or config
DEFAULT_COLUMN_NAMES = [
    "old_gene",
    "old_transcript",
    "new_gene",
    "new_transcript",
    "gffcompare_class_code",
    "exons",
    "class_code_multi",
    "class_type",
    "emckmnj",
    "emckmnje"
]


def parse_synonym_mapping(input_file: Path,
                          column_names: Optional[List[str]] = None,
                          has_header: bool = False) -> pd.DataFrame:
    """
    Parse synonym mapping TSV file.

    Args:
        input_file: Path to input TSV file
        column_names: List of column names (uses DEFAULT_COLUMN_NAMES if None)
        has_header: Whether the file has a header row

    Returns:
        pandas DataFrame with parsed data
    """
    names = column_names or DEFAULT_COLUMN_NAMES

    if has_header:
        df = pd.read_csv(input_file, sep='\t')
    else:
        df = pd.read_csv(input_file, sep='\t', header=None, names=names)

    return df


def count_unique_new_genes(df: pd.DataFrame,
                             ref_col: str = 'old_gene',
                             query_col: str = 'new_gene') -> pd.DataFrame:
    """
    Count unique query genes for each reference gene.

    Args:
        df: Input DataFrame
        ref_col: Name of reference gene column
        query_col: Name of query gene column

    Returns:
        DataFrame with counts per reference gene
    """
    result = df.groupby(ref_col)[query_col].nunique().reset_index()
    result.columns = [ref_col, 'unique_new_gene_count']
    result = result.sort_values(ref_col)
    return result


def print_summary_statistics(counts_df: pd.DataFrame,
                             count_col: str = 'unique_new_gene_count') -> None:
    """
    Print summary statistics for query gene counts.

    Args:
        counts_df: DataFrame with counts
        count_col: Name of count column
    """
    print(f"\n# Total reference genes: {len(counts_df)}", file=sys.stderr)
    print(f"# Min unique query genes: {counts_df[count_col].min()}", file=sys.stderr)
    print(f"# Max unique query genes: {counts_df[count_col].max()}", file=sys.stderr)
    print(f"# Average unique query genes: {counts_df[count_col].mean():.2f}", file=sys.stderr)
    print(f"# Median unique query genes: {counts_df[count_col].median():.2f}", file=sys.stderr)

    print(f"\n# Distribution of unique query gene counts:", file=sys.stderr)
    print(counts_df[count_col].value_counts().sort_index().to_string(), file=sys.stderr)


def main(args):
    """Main function"""
    # Parse column names if provided
    column_names = None
    if args.columns:
        column_names = args.columns.split(',')

    # Load data
    df = parse_synonym_mapping(
        Path(args.input_tsv),
        column_names=column_names,
        has_header=args.header
    )

    if args.count_unique:
        # Count unique query genes per reference gene
        counts = count_unique_new_genes(
            df,
            ref_col=args.ref_col,
            query_col=args.query_col
        )
        print(counts.to_csv(sep='\t', index=False))
        print_summary_statistics(counts)
    else:
        # Just output the parsed data
        print(df.to_csv(sep='\t', index=False))


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Parse synonym mapping files for PAVprot analysis"
    )

    parser.add_argument(
        "--input_tsv", "-i",
        required=True,
        help="Input TSV file"
    )

    parser.add_argument(
        "--columns", "-c",
        help="Comma-separated list of column names (default: uses standard PAVprot columns)"
    )

    parser.add_argument(
        "--header",
        action="store_true",
        help="Input file has a header row"
    )

    parser.add_argument(
        "--count-unique",
        action="store_true",
        dest="count_unique",
        help="Count unique query genes per reference gene"
    )

    parser.add_argument(
        "--ref-col",
        default="old_gene",
        dest="ref_col",
        help="Reference gene column name (default: old_gene)"
    )

    parser.add_argument(
        "--query-col",
        default="new_gene",
        dest="query_col",
        help="Query gene column name (default: new_gene)"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
