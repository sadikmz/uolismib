#!/usr/bin/env python3
"""
InterProScan Output Parser
Parses InterProScan TSV output files and optionally runs InterProScan.
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional
import pandas as pd


class InterProParser:
    """Parser for InterProScan TSV output files"""

    def __init__(self, gff_file: Optional[str] = None):
        """
        Initialize InterProParser.

        Args:
            gff_file: Optional path to GFF3 file for gene-transcript mapping.
                     If provided, gene_id column will be added to outputs by extracting from GFF.
                     If not provided, gene_id column will not be added.
        """
        self.data = None
        self.transcript_to_gene_map = None

        if gff_file:
            print(f"Loading gene-transcript mapping from {gff_file}...")
            self.transcript_to_gene_map = self.transcript_to_geneMap(gff_file)
            print(f"Loaded {len(self.transcript_to_gene_map)} transcript-to-gene mappings")

    @staticmethod
    def transcript_to_geneMap(gff_file: str) -> Dict[str, str]:
        """
        Parse GFF3 file to create a mapping of protein/transcript IDs to gene IDs.

        Handles NCBI and non-NCBI formats:
        - Non-NCBI (e.g., VEuPathDB): Parse mRNA features only
          If ID=FOZG_00001-t36_1;Parent=FOZG_00001;...,
          transcript_id would be FOZG_00001-t36_1 and gene_id would be FOZG_00001.

        - NCBI format: Parse both mRNA and CDS features
          mRNA: ID=rna-XM_059609290.1;Parent=gene-FOBCDRAFT_209856;Name=XM_059609290.1;...
                → transcript_id: XM_059609290.1, gene_id: gene-FOBCDRAFT_209856
          CDS:  ID=cds-XP_059464304.1;Parent=rna-XM_059608890.1;Name=XP_059464304.1;...
                → protein_id: XP_059464304.1 → gene_id (via mRNA parent)

        Args:
            gff_file: Path to the GFF3 file

        Returns:
            Dictionary mapping protein/transcript IDs to gene IDs
        """
        transcript_to_gene_map = {}
        mrna_to_gene = {}  # For NCBI: mRNA ID → gene ID

        # First pass: Parse mRNA features
        with open(gff_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue

                feature_type = parts[2]

                if feature_type == "mRNA":
                    attrs = parts[8]
                    mrna_id = parent_val = transcript_id = None

                    # NCBI format: ID=rna-*, use Name for transcript_id
                    if 'ID=rna' in attrs:
                        for attr in attrs.split(';'):
                            if '=' not in attr:
                                continue
                            key, value = attr.split('=', 1)

                            if key == 'ID':
                                mrna_id = value
                            elif key == 'Parent':
                                parent_val = value
                            elif key == "Name":
                                transcript_id = value

                        if mrna_id and parent_val:
                            mrna_to_gene[mrna_id] = parent_val
                        if transcript_id and parent_val:
                            transcript_to_gene_map[transcript_id] = parent_val

                    # for VEuPathDB or Non-NCBI format: use ID
                    else:
                        for attr in attrs.split(';'):
                            if '=' not in attr:
                                continue

                            key, value = attr.split('=', 1)
                            if key == 'Parent':
                                parent_val = value
                            elif key == "ID":
                                transcript_id = value

                        if transcript_id and parent_val:
                            transcript_to_gene_map[transcript_id] = parent_val

        # Second pass: Parse CDS features (for NCBI format to get protein IDs)
        with open(gff_file, 'r') as f:
            for line in f:
                if line.startswith('#') or not line.strip():
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue

                feature_type = parts[2]

                if feature_type == "CDS":
                    attrs = parts[8]

                    # NCBI format: ID=cds-*, use Name for protein_id
                    if 'ID=cds-' in attrs:
                        protein_id = mrna_parent = None

                        for attr in attrs.split(';'):
                            if '=' not in attr:
                                continue
                            key, value = attr.split('=', 1)

                            if key == 'Parent':
                                mrna_parent = value
                            elif key == 'Name' or key == 'protein_id':
                                if not protein_id:  # Prefer Name
                                    protein_id = value

                        # Map protein_id → gene_id via mRNA parent
                        if protein_id and mrna_parent and mrna_parent in mrna_to_gene:
                            transcript_to_gene_map[protein_id] = mrna_to_gene[mrna_parent]

        return transcript_to_gene_map

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

    def total_ipr_length(self) -> Dict[str, int]:
        """
        Calculate the total IPR domain coverage for each gene, handling overlapping intervals.

        This function merges overlapping IPR domains before calculating the total length,
        preventing double-counting of overlapping regions.

        Returns:
            Dictionary mapping gene_id (or protein_accession if no gene mapping) to total IPR coverage length
            Example: {'FOZG_00001': 280, 'FOZG_01645': 341, ...}

        Note:
            - Intervals are merged if they overlap or are adjacent
            - Coverage is calculated per gene/protein after merging
            - Returns a single numeric value per unique transcript/gene ID
        """
        if self.data is None or len(self.data) == 0:
            return {}

        df = self.data.copy()

        # Filter to only IPR domains
        ipr_df = df[df['interpro_accession'].str.startswith('IPR', na=False)].copy()

        if len(ipr_df) == 0:
            return {}

        # Determine grouping column
        if self.transcript_to_gene_map:
            ipr_df['gene_id'] = ipr_df['protein_accession'].map(self.transcript_to_gene_map)
            group_col = 'gene_id'
        else:
            group_col = 'protein_accession'

        # Calculate coverage with overlap handling for each group
        coverage_dict = {}

        for group_id, group_df in ipr_df.groupby(group_col):
            # Extract intervals (start, end)
            intervals = list(zip(group_df['start_location'], group_df['stop_location']))

            # Calculate total coverage by merging overlapping intervals
            coverage = self._calculate_interval_coverage(intervals)
            coverage_dict[group_id] = coverage

        return coverage_dict

    @staticmethod
    def _calculate_interval_coverage(intervals: list) -> int:
        """
        Calculate total coverage by merging overlapping intervals.

        Args:
            intervals: List of tuples (start, end) where coordinates are inclusive

        Returns:
            Total length covered (sum of merged interval lengths)
        """
        if not intervals:
            return 0

        # Sort intervals by start position
        sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))

        # Merge overlapping intervals
        merged = []
        current_start, current_end = sorted_intervals[0]

        for start, end in sorted_intervals[1:]:
            # Check if intervals overlap or are adjacent
            if start <= current_end + 1:
                # Overlapping or adjacent - extend current interval
                current_end = max(current_end, end)
            else:
                # No overlap - save current interval and start new one
                merged.append((current_start, current_end))
                current_start, current_end = start, end

        # Add the last interval
        merged.append((current_start, current_end))

        # Calculate total length (inclusive coordinates)
        total_length = sum(end - start + 1 for start, end in merged)

        return total_length

    def domain_distribution(self) -> pd.DataFrame:
        """
        Generate domain distribution statistics for each transcript.

        For each domain in each transcript, calculates:
        - domain length
        - whether it's the longest IPR domain for that transcript
        - whether multiple IPR domains share the maximum length
        - total IPR domain length for the transcript/gene

        Returns:
            DataFrame with columns: protein_accession, gene_id (if GFF provided),
            domain_name, domain_length, score, start, stop, rank,
            is_longest_ipr_transcript, multiple_longest_ipr_transcript, total_ipr_length
        """
        if self.data is None or len(self.data) == 0:
            return pd.DataFrame()

        df = self.data.copy()

        # Calculate domain length
        df['domain_length'] = df['stop_location'] - df['start_location'] + 1

        # Get domain name (prefer description, fallback to accession)
        df['domain_name'] = df['signature_description'].where(
            df['signature_description'] != '',
            df['signature_accession']
        )

        # Sort by protein and domain length (descending)
        domain_stats = df.sort_values(
            ['protein_accession', 'domain_length'],
            ascending=[True, False]
        ).copy()

        # Add rank within each protein
        domain_stats['rank'] = domain_stats.groupby('protein_accession').cumcount() + 1

        # Find longest IPR domain for each transcript
        ipr_df = df[df['interpro_accession'].str.startswith('IPR', na=False)].copy()

        if len(ipr_df) > 0:
            # Get max IPR length for each transcript
            max_ipr_lengths = ipr_df.groupby('protein_accession')['domain_length'].max()

            # Count how many domains have the max length for each transcript
            ipr_with_max = ipr_df.merge(
                max_ipr_lengths.rename('max_ipr_length'),
                left_on='protein_accession',
                right_index=True
            )
            ipr_with_max['is_max'] = ipr_with_max['domain_length'] == ipr_with_max['max_ipr_length']
            count_max = ipr_with_max.groupby('protein_accession')['is_max'].sum()

            # Create mapping for is_longest_ipr_transcript
            domain_stats = domain_stats.merge(
                max_ipr_lengths.rename('max_ipr_length'),
                left_on='protein_accession',
                right_index=True,
                how='left'
            )

            # Add is_longest_ipr_transcript column
            domain_stats['is_longest_ipr_transcript'] = (
                (domain_stats['interpro_accession'].str.startswith('IPR', na=False)) &
                (domain_stats['domain_length'] == domain_stats['max_ipr_length'])
            )

            # Add multiple_longest_ipr_transcript column
            domain_stats = domain_stats.merge(
                count_max.rename('count_max_ipr'),
                left_on='protein_accession',
                right_index=True,
                how='left'
            )
            domain_stats['multiple_longest_ipr_transcript'] = (
                domain_stats['is_longest_ipr_transcript'] &
                (domain_stats['count_max_ipr'] > 1)
            )

            # Calculate total IPR domain length per protein with overlap handling
            total_ipr_lengths = {}
            for protein_acc, protein_df in ipr_df.groupby('protein_accession'):
                intervals = list(zip(protein_df['start_location'], protein_df['stop_location']))
                total_ipr_lengths[protein_acc] = self._calculate_interval_coverage(intervals)
            total_ipr_lengths = pd.Series(total_ipr_lengths)

            # Drop temporary columns
            domain_stats = domain_stats.drop(columns=['max_ipr_length', 'count_max_ipr'])
        else:
            # No IPR domains found
            domain_stats['is_longest_ipr_transcript'] = False
            domain_stats['multiple_longest_ipr_transcript'] = False
            total_ipr_lengths = pd.Series(dtype='int64')

        # Add total IPR length per protein first (always calculate this)
        if len(total_ipr_lengths) > 0:
            domain_stats['total_ipr_length'] = domain_stats['protein_accession'].map(total_ipr_lengths)
        else:
            domain_stats['total_ipr_length'] = 0

        # Add gene_id if mapping is available
        if self.transcript_to_gene_map:
            domain_stats['gene_id'] = domain_stats['protein_accession'].map(self.transcript_to_gene_map)

            # Reorder columns to put gene_id after protein_accession
            cols = ['protein_accession', 'gene_id', 'domain_name', 'domain_length',
                   'score', 'start_location', 'stop_location', 'rank',
                   'is_longest_ipr_transcript', 'multiple_longest_ipr_transcript', 'total_ipr_length']
        else:
            cols = ['protein_accession', 'domain_name', 'domain_length',
                   'score', 'start_location', 'stop_location', 'rank',
                   'is_longest_ipr_transcript', 'multiple_longest_ipr_transcript', 'total_ipr_length']

        # Fill NaN values in total_ipr_length with 0
        domain_stats['total_ipr_length'] = domain_stats['total_ipr_length'].fillna(0).astype('int64')

        # Select and rename columns
        domain_stats = domain_stats[cols].rename(columns={
            'start_location': 'start',
            'stop_location': 'stop',
            'domain_length': 'length',
            'domain_name': 'domain'
        })

        return domain_stats


def write_parsed_tsv(results: pd.DataFrame, filepath: str, include_header: bool = False):
    """
    Write standard parsed results to TSV file in 15-column format.

    Output format is 15 columns (standard InterProScan format):
    - Columns 1-13: Standard InterProScan fields
    - Column 14: GO annotations
    - Column 15: Pathway annotations
    """
    results.to_csv(filepath, sep='\t', index=False, header=include_header)


def write_domain_stats_tsv(domain_stats: pd.DataFrame, filepath: str):
    """
    Write domain distribution statistics to TSV file.

    Args:
        domain_stats: DataFrame with domain statistics
        filepath: Output TSV file path
    """
    domain_stats.to_csv(
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
        suffix: Descriptive suffix (e.g., 'domain_distribution', 'total_ipr_length')
        extension: File extension (e.g., 'tsv')

    Returns:
        Generated filename: basename_suffix.extension
    """
    input_path = Path(input_file)
    basename = input_path.stem
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
        '--run-interproscan',
        action='store_true',
        help='Run InterProScan before parsing'
    )

    # InterProScan run arguments
    parser.add_argument(
        '-i', '--input',
        help='Input protein FASTA file (required if --run-interproscan is used)'
    )
    parser.add_argument(
        '--cpu',
        type=int,
        default=4,
        help='Number of CPUs to use for InterProScan (default: 4)'
    )
    parser.add_argument(
        '-b', '--output-base',
        help='Output file basename for InterProScan (default: basename of input file)'
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
        help='Include pathway annotations'
    )
    parser.add_argument(
        '--databases',
        help='Databases to search (comma-separated list, default: all)'
    )

    # Parsing arguments
    parser.add_argument(
        '--parse',
        help='InterProScan TSV output file to parse (optional if --run-interproscan is used)'
    )
    parser.add_argument(
        '--gff',
        help='Optional GFF3 file for gene-transcript mapping (used to add gene_id to domain_distribution output)'
    )

    # Output options
    parser.add_argument(
        '--output',
        help='Output file path for total_ipr_length (default: <basename>_total_ipr_length.tsv)'
    )
    parser.add_argument(
        '--domain-distribution',
        help='Output file for domain distribution statistics (default: <basename>_domain_distribution.tsv when --parse is used)'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.run_interproscan:
        if not args.input:
            parser.error("--run-interproscan requires --input argument")

        # Determine output basename
        if args.output_base:
            output_base = args.output_base
        else:
            output_base = Path(args.input).stem

        # Run InterProScan
        print(f"Running InterProScan for: {args.input}")
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
        print(f"\nParsing InterProScan output: {parse_file}")

    elif args.parse:
        parse_file = args.parse
        print(f"Parsing TSV file: {parse_file}")

    else:
        parser.error("Either --run-interproscan or --parse must be specified")

    # Initialize parser with optional GFF
    ipr_parser = InterProParser(gff_file=args.gff)

    # Parse InterProScan TSV
    df = ipr_parser.parse_tsv(parse_file)
    print(f"Loaded {len(df)} InterProScan entries")

    # Calculate total IPR lengths
    print("Calculating total IPR domain lengths per gene...")
    total_lengths = ipr_parser.total_ipr_length()
    print(f"Calculated total IPR lengths for {len(total_lengths)} genes/proteins")

    # Write total IPR length output
    if args.output:
        output_file = args.output
    else:
        output_file = generate_default_filename(parse_file, 'total_ipr_length', 'tsv')

    # Convert dict to DataFrame for output
    result_df = pd.DataFrame(list(total_lengths.items()),
                             columns=['gene_id' if ipr_parser.transcript_to_gene_map else 'protein_accession',
                                     'total_iprdom_len'])
    result_df.to_csv(output_file, sep='\t', index=False)
    print(f"Total IPR length results written to: {output_file}")

    # Generate domain_distribution output only when --parse is explicitly specified
    if args.parse:
        print("\nGenerating domain distribution statistics...")
        domain_stats = ipr_parser.domain_distribution()

        if len(domain_stats) > 0:
            if args.domain_distribution:
                domain_dist_file = args.domain_distribution
            else:
                domain_dist_file = generate_default_filename(parse_file, 'domain_distribution', 'tsv')

            write_domain_stats_tsv(domain_stats, domain_dist_file)
            print(f"Domain distribution written to: {domain_dist_file}")

            # Print summary statistics
            if 'is_longest_ipr_transcript' in domain_stats.columns:
                n_longest = domain_stats['is_longest_ipr_transcript'].sum()
                n_multiple = domain_stats['multiple_longest_ipr_transcript'].sum()
                print(f"  - {n_longest} domains are longest IPR for their transcript")
                print(f"  - {n_multiple} transcripts have multiple longest IPR domains")
        else:
            print("No domain data to write")


if __name__ == '__main__':
    main()
