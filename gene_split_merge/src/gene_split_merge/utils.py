#!/usr/bin/env python3
"""
DIAMOND Utilities Module
=========================
Enhanced utilities for DIAMOND operations including database management,
output parsing, and advanced analysis functions.

Borrowed and enhanced from diamondonpy with improvements for genomics workflows.

Author: Bioinformatics Workflow
Date: 2025-12-06
"""

import subprocess
import pandas as pd
import logging
import tempfile
import os
from typing import Union, List, Dict, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiamondDatabaseManager:
    """
    Manage DIAMOND database creation and information retrieval.
    """

    def __init__(self, executable: str = "diamond"):
        """
        Initialize the database manager.

        Args:
            executable: Path to the diamond executable
        """
        self.executable = executable

    def makedb(self,
               input_fasta: str,
               output_db: str,
               threads: int = 28,
               taxonmap: Optional[str] = None,
               taxonnodes: Optional[str] = None,
               taxonnames: Optional[str] = None) -> str:
        """
        Create a DIAMOND database from a FASTA file.

        Args:
            input_fasta: Input protein FASTA file
            output_db: Output database file (.dmnd)
            threads: Number of CPU threads
            taxonmap: Protein accession to taxid mapping file (optional)
            taxonnodes: Taxonomy nodes.dmp from NCBI (optional)
            taxonnames: Taxonomy names.dmp from NCBI (optional)

        Returns:
            Path to created database
        """
        logger.info(f"Creating DIAMOND database: {output_db}")

        cmd = [
            self.executable, 'makedb',
            '--in', input_fasta,
            '--db', output_db,
            '--threads', str(threads)
        ]

        if taxonmap:
            cmd.extend(['--taxonmap', taxonmap])
        if taxonnodes:
            cmd.extend(['--taxonnodes', taxonnodes])
        if taxonnames:
            cmd.extend(['--taxonnames', taxonnames])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Database created successfully: {output_db}")
            return output_db

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create database: {e.stderr}"
            logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    def dbinfo(self, database: str) -> Dict[str, any]:
        """
        Get information about a DIAMOND database.

        Args:
            database: Path to DIAMOND database

        Returns:
            Dictionary with database information
        """
        logger.info(f"Getting info for database: {database}")

        cmd = [self.executable, 'dbinfo', '--db', database]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse output
            info = {}
            for line in result.stdout.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()

            return info

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get database info: {e.stderr}")
            raise RuntimeError(e.stderr) from e


class DiamondOutputParser:
    """
    Parse and process DIAMOND output in various formats.
    """

    # Default DIAMOND tabular columns (outfmt 6)
    DEFAULT_COLUMNS = [
        'qseqid', 'sseqid', 'pident', 'length', 'mismatch',
        'gapopen', 'qstart', 'qend', 'sstart', 'send',
        'evalue', 'bitscore'
    ]

    @staticmethod
    def parse_tabular(output_file: str,
                     columns: Optional[List[str]] = None,
                     add_coverage: bool = True) -> pd.DataFrame:
        """
        Parse DIAMOND tabular output (outfmt 6).

        Args:
            output_file: Path to DIAMOND output file
            columns: Column names (if None, uses DEFAULT_COLUMNS)
            add_coverage: Calculate and add query/subject coverage columns

        Returns:
            DataFrame with parsed results
        """
        if columns is None:
            columns = DiamondOutputParser.DEFAULT_COLUMNS.copy()

        logger.info(f"Parsing DIAMOND output: {output_file}")

        try:
            df = pd.read_csv(output_file, sep='\t', names=columns, comment='#')

            # Convert numeric columns
            numeric_cols = ['pident', 'length', 'mismatch', 'gapopen',
                          'qstart', 'qend', 'sstart', 'send', 'bitscore']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # Handle evalue (scientific notation)
            if 'evalue' in df.columns:
                df['evalue'] = pd.to_numeric(df['evalue'], errors='coerce')

            # Add coverage if requested and if qlen/slen are available
            if add_coverage and 'qlen' in df.columns and 'slen' in df.columns:
                df['qcoverage'] = (df['length'] / df['qlen']) * 100
                df['scoverage'] = (df['length'] / df['slen']) * 100

            logger.info(f"Parsed {len(df)} alignments")
            return df

        except Exception as e:
            logger.error(f"Failed to parse output: {e}")
            raise

    @staticmethod
    def filter_by_quality(df: pd.DataFrame,
                         min_identity: float = 30.0,
                         min_coverage: float = 50.0,
                         max_evalue: float = 1e-5) -> pd.DataFrame:
        """
        Filter DIAMOND results by quality thresholds.

        Args:
            df: DataFrame from parse_tabular
            min_identity: Minimum percent identity
            min_coverage: Minimum query coverage
            max_evalue: Maximum e-value

        Returns:
            Filtered DataFrame
        """
        original_count = len(df)

        filtered = df[
            (df['pident'] >= min_identity) &
            (df['evalue'] <= max_evalue)
        ].copy()

        if 'qcoverage' in filtered.columns:
            filtered = filtered[filtered['qcoverage'] >= min_coverage]

        logger.info(f"Filtered {original_count} hits to {len(filtered)} high-quality hits")

        return filtered

    @staticmethod
    def get_best_hits(df: pd.DataFrame,
                      by: str = 'evalue',
                      keep: str = 'first') -> pd.DataFrame:
        """
        Get best hit for each query sequence.

        Args:
            df: DataFrame from parse_tabular
            by: Column to sort by ('evalue', 'bitscore', 'pident')
            keep: Which duplicate to keep ('first', 'last')

        Returns:
            DataFrame with one row per query (best hit)
        """
        if by == 'evalue':
            ascending = True
        elif by in ['bitscore', 'pident']:
            ascending = False
        else:
            raise ValueError(f"Invalid 'by' parameter: {by}")

        # Sort by the specified column
        sorted_df = df.sort_values(by, ascending=ascending)

        # Keep first (best) hit for each query
        best_hits = sorted_df.drop_duplicates(subset='qseqid', keep=keep)

        logger.info(f"Selected {len(best_hits)} best hits from {len(df)} total hits")

        return best_hits


class DiamondAlignmentAnalyzer:
    """
    Advanced analysis of DIAMOND alignment results.
    """

    @staticmethod
    def calculate_alignment_statistics(df: pd.DataFrame) -> Dict[str, any]:
        """
        Calculate comprehensive statistics from DIAMOND alignments.

        Args:
            df: DataFrame from DiamondOutputParser.parse_tabular

        Returns:
            Dictionary with alignment statistics
        """
        stats = {
            'total_alignments': len(df),
            'unique_queries': df['qseqid'].nunique(),
            'unique_subjects': df['sseqid'].nunique(),
            'avg_identity': df['pident'].mean(),
            'median_identity': df['pident'].median(),
            'avg_length': df['length'].mean(),
            'avg_evalue': df['evalue'].mean(),
            'avg_bitscore': df['bitscore'].mean()
        }

        if 'qcoverage' in df.columns:
            stats['avg_query_coverage'] = df['qcoverage'].mean()
        if 'scoverage' in df.columns:
            stats['avg_subject_coverage'] = df['scoverage'].mean()

        # Count queries with hits
        queries_with_hits = df.groupby('qseqid').size()
        stats['queries_with_1_hit'] = (queries_with_hits == 1).sum()
        stats['queries_with_multiple_hits'] = (queries_with_hits > 1).sum()
        stats['avg_hits_per_query'] = queries_with_hits.mean()

        return stats

    @staticmethod
    def identify_paralogs(df: pd.DataFrame,
                         min_identity: float = 70.0,
                         min_hits: int = 2) -> pd.DataFrame:
        """
        Identify potential paralogs (queries with multiple high-quality hits).

        Args:
            df: DataFrame from DiamondOutputParser.parse_tabular
            min_identity: Minimum identity to consider
            min_hits: Minimum number of hits to call paralogs

        Returns:
            DataFrame with queries that have multiple hits (potential paralogs)
        """
        # Filter by identity
        high_quality = df[df['pident'] >= min_identity].copy()

        # Count hits per query
        hit_counts = high_quality.groupby('qseqid').size()
        paralogs_queries = hit_counts[hit_counts >= min_hits].index

        # Get all hits for paralog candidates
        paralogs_df = high_quality[high_quality['qseqid'].isin(paralogs_queries)]

        logger.info(f"Identified {len(paralogs_queries)} queries with {min_hits}+ hits (potential paralogs)")

        return paralogs_df.sort_values(['qseqid', 'pident'], ascending=[True, False])

    @staticmethod
    def build_alignment_graph(df: pd.DataFrame,
                            min_identity: float = 50.0) -> Dict[str, List[str]]:
        """
        Build a graph representation of alignments.

        Args:
            df: DataFrame from DiamondOutputParser.parse_tabular
            min_identity: Minimum identity threshold

        Returns:
            Dictionary mapping query IDs to lists of subject IDs
        """
        filtered = df[df['pident'] >= min_identity]

        graph = {}
        for _, row in filtered.iterrows():
            query = row['qseqid']
            subject = row['sseqid']

            if query not in graph:
                graph[query] = []
            graph[query].append(subject)

        return graph


class DiamondWorkflowHelper:
    """
    Helper functions for common DIAMOND workflows.
    """

    def __init__(self, executable: str = "diamond"):
        """
        Initialize the workflow helper.

        Args:
            executable: Path to the diamond executable
        """
        self.executable = executable
        self.db_manager = DiamondDatabaseManager(executable)

    def run_blastp(self,
                   query: str,
                   database: str,
                   output: str,
                   evalue: float = 1e-10,
                   max_target_seqs: int = 25,
                   threads: int = 28,
                   sensitivity: str = "ultra-sensitive",
                   outfmt: str = "6") -> pd.DataFrame:
        """
        Run DIAMOND BLASTP with sensible defaults.

        Args:
            query: Query protein FASTA file
            database: DIAMOND database (.dmnd)
            output: Output file
            evalue: Maximum e-value
            max_target_seqs: Maximum targets per query
            threads: Number of CPU threads
            sensitivity: Sensitivity mode (ultra-sensitive, very-sensitive, etc.)
            outfmt: Output format

        Returns:
            DataFrame with parsed results
        """
        logger.info(f"Running DIAMOND BLASTP: {query} vs {database}")

        cmd = [
            self.executable, 'blastp',
            '--query', query,
            '--db', database,
            '--out', output,
            '--outfmt', outfmt,
            '--evalue', str(evalue),
            '--max-target-seqs', str(max_target_seqs),
            '--threads', str(threads),
            f'--{sensitivity}'
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"BLASTP completed successfully")

            # Parse output
            return DiamondOutputParser.parse_tabular(output)

        except subprocess.CalledProcessError as e:
            logger.error(f"BLASTP failed: {e.stderr}")
            raise RuntimeError(e.stderr) from e

    def create_and_align(self,
                        query: str,
                        subject: str,
                        output_dir: str,
                        **kwargs) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Complete workflow: create databases and run bidirectional BLASTP.

        Args:
            query: Query protein FASTA
            subject: Subject protein FASTA
            output_dir: Directory for outputs
            **kwargs: Additional arguments for run_blastp

        Returns:
            Tuple of (forward_df, reverse_df)
        """
        os.makedirs(output_dir, exist_ok=True)

        query_db = os.path.join(output_dir, "query_db.dmnd")
        subject_db = os.path.join(output_dir, "subject_db.dmnd")
        forward_out = os.path.join(output_dir, "forward.tsv")
        reverse_out = os.path.join(output_dir, "reverse.tsv")

        # Create databases
        logger.info("Creating databases...")
        self.db_manager.makedb(query, query_db)
        self.db_manager.makedb(subject, subject_db)

        # Run alignments
        logger.info("Running forward alignment...")
        forward_df = self.run_blastp(query, subject_db, forward_out, **kwargs)

        logger.info("Running reverse alignment...")
        reverse_df = self.run_blastp(subject, query_db, reverse_out, **kwargs)

        return forward_df, reverse_df


def main():
    """Example usage of DIAMOND utilities."""
    print("DIAMOND Utilities Module")
    print("=" * 60)
    print("\nThis module provides utilities for DIAMOND operations.")
    print("\nExample usage:")
    print("""
from .utils import DiamondWorkflowHelper, DiamondOutputParser

# Initialize helper
helper = DiamondWorkflowHelper()

# Complete workflow: create DBs and run bidirectional BLASTP
forward_df, reverse_df = helper.create_and_align(
    query="reference_proteins.fasta",
    subject="updated_proteins.fasta",
    output_dir="results/",
    threads=28,
    sensitivity="ultra-sensitive"
)

# Filter results
filtered = DiamondOutputParser.filter_by_quality(
    forward_df,
    min_identity=70.0,
    min_coverage=70.0
)

# Get best hits
best_hits = DiamondOutputParser.get_best_hits(filtered, by='evalue')

print(f"Total hits: {len(forward_df)}")
print(f"High-quality hits: {len(filtered)}")
print(f"Best hits: {len(best_hits)}")
    """)
    print("=" * 60)


if __name__ == '__main__':
    main()
