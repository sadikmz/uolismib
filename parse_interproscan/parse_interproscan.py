#!/usr/bin/env python3
"""
InterProScan Output Parser
Parses InterProScan TSV output files and optionally runs InterProScan.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Tuple
import pandas as pd


class InterProParser:
    """Parser for InterProScan TSV output files"""

    def __init__(self):
        self.data = None

    def parse_tsv(self, filepath: str) -> pd.DataFrame:
        """
        Parse TSV format InterProScan output (15-column format) using pandas.

        Standard InterProScan TSV is always 15 columns:
        - Columns 1-13: Core annotation data
        - Column 14: GO terms
        - Column 15: Pathway annotations

        Missing values are represented as "-" (dash) and are converted to empty strings.

        Args:
            filepath: Path to TSV file

        Returns:
            pandas DataFrame containing parsed data
        """
        # Define column names for InterProScan TSV format
        columns = [
            'protein_accession', 'md5_digest', 'sequence_length', 'analysis',
            'signature_accession', 'signature_description', 'start_location',
            'stop_location', 'score', 'status', 'date', 'interpro_accession',
            'interpro_description', 'go_annotations', 'pathway_annotations'
        ]

        # Read TSV file
        df = pd.read_csv(
            filepath,
            sep='\t',
            names=columns,
            comment='#',
            na_values='-',
            keep_default_na=False,
            dtype={
                'protein_accession': str,
                'md5_digest': str,
                'sequence_length': 'Int64',  # Nullable integer
                'analysis': str,
                'signature_accession': str,
                'signature_description': str,
                'start_location': 'Int64',
                'stop_location': 'Int64',
                'score': str,
                'status': str,
                'date': str,
                'interpro_accession': str,
                'interpro_description': str,
                'go_annotations': str,
                'pathway_annotations': str
            }
        )

        # Replace NaN with empty strings
        df = df.fillna('')

        self.data = df
        return df

    def longest_domain(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Select proteins with longest domain when multiple domains match.
        Splits results into IPR and non-IPR proteins based on whether
        the longest IPR domain matches the overall longest domain.

        Returns:
            Tuple of (ipr_results, non_ipr_results, domain_length_distribution)
            - ipr_results: Proteins where longest IPR domain IS the overall longest (IPRorNot="yes")
            - non_ipr_results: Proteins where longest IPR domain is NOT the overall longest (IPRorNot="no")
            - domain_length_distribution: DataFrame with all domains ranked by length
        """
        df = self.data.copy()

        # Calculate domain length
        df['domain_length'] = df['stop_location'] - df['start_location'] + 1

        # Get domain name (prefer description, fallback to accession)
        df['domain_name'] = df['signature_description'].where(
            df['signature_description'] != '',
            df['signature_accession']
        )

        # Find longest domain for each protein (overall)
        idx_longest = df.groupby('protein_accession')['domain_length'].idxmax()
        longest_df = df.loc[idx_longest].copy()

        # Add longestDom column (overall longest domain)
        longest_df['longestDom'] = longest_df['domain_name']

        # Find longest IPR domain for each protein
        ipr_df = df[df['interpro_accession'].str.startswith('IPR', na=False)].copy()
        if len(ipr_df) > 0:
            idx_longest_ipr = ipr_df.groupby('protein_accession')['domain_length'].idxmax()
            longest_ipr_df = ipr_df.loc[idx_longest_ipr][['protein_accession', 'domain_name']].copy()
            longest_ipr_df.rename(columns={'domain_name': 'longestIPRdom'}, inplace=True)

            # Merge with main results
            longest_df = longest_df.merge(longest_ipr_df, on='protein_accession', how='left')
        else:
            longest_df['longestIPRdom'] = ''

        # Fill NaN in longestIPRdom with empty string (for proteins without IPR domains)
        longest_df['longestIPRdom'] = longest_df['longestIPRdom'].fillna('')

        # Add IPRorNot column: "yes" if longestIPRdom matches longestDom, "no" otherwise
        # This tracks whether the longest IPR domain is also the overall longest domain
        longest_df['IPRorNot'] = longest_df.apply(
            lambda row: 'yes' if row['longestIPRdom'] != '' and row['longestIPRdom'] == row['longestDom'] else 'no',
            axis=1
        )

        # Split into IPR and non-IPR results
        ipr_results = longest_df[longest_df['IPRorNot'] == 'yes'].copy()
        non_ipr_results = longest_df[longest_df['IPRorNot'] == 'no'].copy()

        # Create domain statistics DataFrame
        domain_stats = df.sort_values(
            ['protein_accession', 'domain_length'],
            ascending=[True, False]
        ).copy()

        # Add rank within each protein
        domain_stats['rank'] = domain_stats.groupby('protein_accession').cumcount() + 1

        # Select relevant columns for stats
        domain_stats = domain_stats[['protein_accession', 'domain_name', 'domain_length',
            'score', 'start_location', 'stop_location', 'rank']].rename(columns={'start_location': 'start','stop_location': 'stop', 'domain_length': 'length','domain_name': 'domain'})

        return ipr_results, non_ipr_results, domain_stats


def write_parsed_tsv(results: pd.DataFrame, filepath: str, include_header: bool = False):
    """
    Write standard parsed results to TSV file in 15-column format.

    Output format is 15 columns (standard InterProScan format):
    - Columns 1-13: Standard InterProScan fields
    - Column 14: GO annotations
    - Column 15: Pathway annotations

    Args:
        results: DataFrame with results
        filepath: Output TSV file path
        include_header: Include column headers in output (default: False)
    """
    # Define column order for standard output
    output_columns = [
        'protein_accession', 'md5_digest', 'sequence_length', 'analysis',
        'signature_accession', 'signature_description', 'start_location',
        'stop_location', 'score', 'status', 'date', 'interpro_accession',
        'interpro_description', 'go_annotations', 'pathway_annotations'
    ]

    # Write to TSV with optional header
    results[output_columns].to_csv(
        filepath,
        sep='\t',
        header=include_header,
        index=False,
        na_rep=''
    )


def write_longest_results_tsv(results: pd.DataFrame, filepath: str, include_header: bool = False):
    """
    Write longest domain results to TSV file in 18-column format.

    Output format is 18 columns:
    - Columns 1-13: Standard InterProScan fields
    - Column 14: GO annotations
    - Column 15: Pathway annotations
    - Column 16: longestDom (name of longest domain overall)
    - Column 17: longestIPRdom (name of longest IPR domain)
    - Column 18: IPRorNot (yes/no if domain starts with IPR)

    Args:
        results: DataFrame with results
        filepath: Output TSV file path
        include_header: Include column headers in output (default: False)
    """
    # Define column order for output
    output_columns = [
        'protein_accession', 'md5_digest', 'sequence_length', 'analysis',
        'signature_accession', 'signature_description', 'start_location',
        'stop_location', 'score', 'status', 'date', 'interpro_accession',
        'interpro_description', 'go_annotations', 'pathway_annotations',
        'longestDom', 'longestIPRdom', 'IPRorNot'
    ]

    # Write to TSV with optional header
    results[output_columns].to_csv(
        filepath,
        sep='\t',
        header=include_header,
        index=False,
        na_rep=''
    )


def write_domain_stats_tsv(domain_stats: pd.DataFrame, filepath: str):
    """
    Write domain length distribution to TSV file.

    Args:
        domain_stats: DataFrame with domain statistics
        filepath: Output TSV file path
    """
    # Rename columns to match expected output format
    output_df = domain_stats.rename(columns={
        'domain': 'domain_name',
        'length': 'domain_length'
    })

    # Write to TSV with header
    output_df.to_csv(
        filepath,
        sep='\t',
        index=False,
        na_rep=''
    )


def generate_default_filename(input_file: str, suffix: str, extension: str) -> str:
    """
    Generate default output filename based on input filename.

    Args:
        input_file: Input file path
        suffix: Descriptive suffix (e.g., 'parsed', 'longest_domains', 'domain_distribution')
        extension: File extension (e.g., 'json', 'tsv')

    Returns:
        Generated filename: basename_suffix.extension
    """
    input_path = Path(input_file)
    basename = input_path.stem  # Filename without extension
    return f"{basename}_{suffix}.{extension}"


def run_interproscan(
    protein_file: str,
    cpu: int,
    output_base: str,
    output_format: str,
    pathways: bool = False,
    databases: str = None
) -> bool:
    """
    Run InterProScan on protein sequences.

    Args:
        protein_file: Input FASTA file with protein sequences
        cpu: Number of CPUs to use
        output_base: Output file basename (set via -b option)
        output_format: Output format (TSV, XML, JSON, GFF3)
        pathways: Include pathway annotations
        databases: Databases to search (default to all if unset, or comma-separated list)

    Returns:
        True if successful, False otherwise
    """
    cmd = [
        'interproscan.sh',
        '-i', protein_file,
        '-cpu', str(cpu),
        '-b', output_base,
        '-f', output_format,
        '--iprlookup',
        '--goterms'
    ]

    if pathways:
        cmd.append('--pathways')

    if databases:
        cmd.extend(['-appl', databases])

    print(f"Running InterProScan: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("InterProScan completed successfully")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running InterProScan: {e}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: interproscan.sh not found. Please ensure InterProScan is installed and in PATH.", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Parse InterProScan TSV output or run InterProScan and parse results'
    )

    # Mode selection
    parser.add_argument(
        '--run',
        action='store_true',
        help='Run InterProScan before parsing'
    )

    # InterProScan run arguments
    parser.add_argument(
        '-i', '--input',
        help='Input protein FASTA file (required if --run is used)'
    )
    parser.add_argument(
        '--cpu',
        type=int,
        default=4,
        help='Number of CPUs to use for InterProScan (default: 4)'
    )
    parser.add_argument(
        '-b', '--output-base',
        help='Output file basename for InterProScan (default: basename of input file). InterProScan will append format extension.'
    )
    parser.add_argument(
        '-f', '--format',
        choices=['TSV', 'XML', 'JSON', 'GFF3', 'tsv', 'xml', 'json', 'gff3'],
        default='TSV',
        help='Output format for InterProScan (default: TSV)'
    )
    parser.add_argument(
        '--pathways',
        action='store_true',
        help='Include pathway annotations (Note: --iprlookup and --goterms are always included by default)'
    )
    parser.add_argument(
        '--databases',
        help='Databases to search (default to all if unset, or comma-separated list)'
    )

    # Parsing arguments
    parser.add_argument(
        '--parse',
        help='InterProScan TSV output file to parse'
    )

    # Analysis options
    parser.add_argument(
        '--longest-domain',
        action='store_true',
        help='Select only the longest domain for each protein'
    )
    parser.add_argument(
        '--domain-stats-tsv',
        help='Output file for domain length distribution statistics (TSV). If not specified, defaults to <basename>_domain_distribution.tsv'
    )
    parser.add_argument(
        '--output-parsed-tsv',
        help='Output file for parsed results (TSV). If not specified, defaults to <basename>_parsed.tsv'
    )
    parser.add_argument(
        '--tsv-header',
        action='store_true',
        help='Include column headers in TSV output files (default: False)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.run:
        if not args.input:
            parser.error("--run requires --input argument")

        # Determine output basename
        if args.output_base:
            output_base = args.output_base
        else:
            # Use basename of input file (without extension)
            output_base = Path(args.input).stem

        # Run InterProScan
        print(f"Running complete InterProScan pipeline for: {args.input}")
        print(f"Output basename: {output_base}")
        success = run_interproscan(
            protein_file=args.input,
            cpu=args.cpu,
            output_base=output_base,
            output_format=args.format,
            pathways=args.pathways,
            databases=args.databases
        )

        if not success:
            sys.exit(1)

        # Set parse file to the output (InterProScan appends format extension)
        parse_file = f"{output_base}.{args.format.lower()}"

        # Automatically enable longest-domain analysis for complete pipeline
        args.longest_domain = True
        print(f"\nAutomatically running longest domain analysis...")

    elif args.parse:
        parse_file = args.parse
        print(f"Parsing TSV file: {parse_file}")

    else:
        parser.error("Either --run or --parse must be specified")

    # Parse the TSV file
    interpro = InterProParser()
    results = interpro.parse_tsv(parse_file)

    print(f"Parsed {len(results)} entries")

    # Apply longest domain filter if requested
    domain_stats = None
    non_ipr_results = None

    if args.longest_domain:
        print("Selecting longest domain for each protein...")
        ipr_results, non_ipr_results, domain_stats = interpro.longest_domain()

        total_proteins = len(ipr_results) + len(non_ipr_results)
        print(f"Filtered to {total_proteins} entries (one per protein)")
        print(f"  - {len(ipr_results)} proteins: longest IPR domain is overall longest (IPRorNot=yes)")
        print(f"  - {len(non_ipr_results)} proteins: longest IPR domain is NOT overall longest (IPRorNot=no)")

        # Use ipr_results as the main results for backward compatibility
        results = ipr_results

    # Determine if any output is needed
    output_any = args.domain_stats_tsv or args.output_parsed_tsv

    # Save domain statistics if requested or if longest_domain was used
    if domain_stats is not None:
        # Generate default filenames if not specified
        if args.longest_domain and not output_any:
            # Auto-generate all TSV outputs when --longest-domain is used without explicit outputs
            domain_stats_tsv = generate_default_filename(parse_file, 'domain_distribution', 'tsv')
            output_ipr_tsv = generate_default_filename(parse_file, 'longest_domains', 'tsv')
            output_non_ipr_tsv = generate_default_filename(parse_file, 'non_ipr', 'tsv')

            # Save domain statistics (TSV)
            write_domain_stats_tsv(domain_stats, domain_stats_tsv)
            print(f"Domain statistics saved to {domain_stats_tsv}")

            # Save IPR results (main output)
            if len(ipr_results) > 0:
                write_longest_results_tsv(ipr_results, output_ipr_tsv, args.tsv_header)
                print(f"IPR proteins (longest IPR = overall longest) saved to {output_ipr_tsv}")

            # Save non-IPR results (separate file)
            if len(non_ipr_results) > 0:
                write_longest_results_tsv(non_ipr_results, output_non_ipr_tsv, args.tsv_header)
                print(f"Non-IPR proteins (longest IPR != overall longest) saved to {output_non_ipr_tsv}")
        else:
            # User specified some outputs explicitly
            if args.domain_stats_tsv:
                write_domain_stats_tsv(domain_stats, args.domain_stats_tsv)
                print(f"Domain statistics saved to {args.domain_stats_tsv}")

    # Save parsed results if requested
    if args.output_parsed_tsv:
        if args.longest_domain:
            # Write 18-column format with longest domain info
            write_longest_results_tsv(results, args.output_parsed_tsv, args.tsv_header)
        else:
            # Write standard 15-column format
            write_parsed_tsv(results, args.output_parsed_tsv, args.tsv_header)
        print(f"Parsed results saved to {args.output_parsed_tsv}")
    elif not args.longest_domain and not output_any:
        # Auto-generate parsed output (TSV) when no specific output requested and no longest_domain
        output_parsed_tsv = generate_default_filename(parse_file, 'parsed', 'tsv')
        write_parsed_tsv(results, output_parsed_tsv, args.tsv_header)
        print(f"Parsed results saved to {output_parsed_tsv}")

    # Print summary
    print("\nSummary:")
    print(f"Total entries: {len(results)}")

    if len(results) > 0:
        # Count unique proteins
        unique_proteins = results['protein_accession'].nunique()
        print(f"Unique proteins: {unique_proteins}")

        # Count analyses/databases
        if 'analysis' in results.columns:
            analysis_col = 'analysis'
        elif 'source' in results.columns:
            analysis_col = 'source'
        else:
            analysis_col = None

        if analysis_col:
            analyses = results[analysis_col].value_counts().to_dict()
            print("\nMatches by database:")
            for analysis, count in sorted(analyses.items(), key=lambda x: x[1], reverse=True):
                print(f"  {analysis}: {count}")


if __name__ == '__main__':
    main()
