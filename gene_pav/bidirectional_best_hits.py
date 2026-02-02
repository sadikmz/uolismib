#!/usr/bin/env python3
"""
Bidirectional Best Hit (BBH) Analysis Module

Identifies reciprocal best hits between reference and query proteomes,
which are strong candidates for one-to-one orthologous relationships.

This module is designed to work with pavprot's DIAMOND output and is
structured for future integration with gene_split_merge.GeneStructureAnalyzer.

Usage:
    # As standalone script
    python bidirectional_best_hits.py --fwd ref_vs_qry.tsv.gz --rev qry_vs_ref.tsv.gz

    # From pavprot.py
    from bidirectional_best_hits import BidirectionalBestHits
    bbh = BidirectionalBestHits()
    results = bbh.find_bbh(fwd_diamond, rev_diamond)

Author: Bioinformatics Workflow
Date: 2024-12-19
"""

import gzip
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
from dataclasses import dataclass

import pandas as pd


@dataclass
class BlastHit:
    """Represents a DIAMOND/BLAST alignment hit."""
    query_id: str
    subject_id: str
    pident: float
    length: int
    qstart: int
    qend: int
    qlen: int
    sstart: int
    send: int
    slen: int
    evalue: float
    bitscore: float
    qcovhsp: float
    scovhsp: float

    @property
    def query_coverage(self) -> float:
        """Calculate query coverage percentage."""
        return self.qcovhsp

    @property
    def subject_coverage(self) -> float:
        """Calculate subject coverage percentage."""
        return self.scovhsp


class BidirectionalBestHits:
    """
    Bidirectional Best Hit (BBH) analyzer for ortholog identification.

    BBH (also known as Reciprocal Best Hit, RBH) finds gene pairs where:
    - Gene A's best match in genome B is gene B
    - Gene B's best match in genome A is gene A

    This reciprocal relationship is strong evidence for orthology.

    Attributes:
        forward_df: DataFrame of forward DIAMOND hits (ref -> query)
        reverse_df: DataFrame of reverse DIAMOND hits (query -> ref)
    """

    # DIAMOND outfmt 6 column names (matching pavprot's format)
    DIAMOND_COLUMNS = [
        'qseqid', 'qlen', 'sseqid', 'slen', 'qstart', 'qend',
        'sstart', 'send', 'evalue', 'bitscore', 'score', 'length',
        'pident', 'nident', 'mismatch', 'gapopen', 'gaps',
        'qcovhsp', 'scovhsp', 'qstrand'
    ]

    def __init__(self):
        """Initialize the BBH analyzer."""
        self.forward_df: Optional[pd.DataFrame] = None
        self.reverse_df: Optional[pd.DataFrame] = None
        self._bbh_cache: Optional[pd.DataFrame] = None

    def load_diamond_file(self, filepath: str, compressed: bool = True) -> pd.DataFrame:
        """
        Load DIAMOND output file into DataFrame.

        Args:
            filepath: Path to DIAMOND output (TSV format)
            compressed: Whether file is gzip compressed

        Returns:
            DataFrame with DIAMOND results
        """
        if compressed or filepath.endswith('.gz'):
            opener = lambda f: gzip.open(f, 'rt')
        else:
            opener = lambda f: open(f, 'r')

        records = []
        with opener(filepath) as f:
            for line in f:
                if not line.strip():
                    continue
                parts = line.strip().split('\t')
                if len(parts) < 20:
                    # Handle shorter format (basic outfmt 6)
                    continue

                records.append({
                    'qseqid': parts[0],
                    'qlen': int(parts[1]),
                    'sseqid': parts[2],
                    'slen': int(parts[3]),
                    'qstart': int(parts[4]),
                    'qend': int(parts[5]),
                    'sstart': int(parts[6]),
                    'send': int(parts[7]),
                    'evalue': float(parts[8]),
                    'bitscore': float(parts[9]),
                    'length': int(parts[11]),
                    'pident': float(parts[12]),
                    'nident': int(parts[13]),
                    'qcovhsp': float(parts[17]),
                    'scovhsp': float(parts[18])
                })

        df = pd.DataFrame(records)
        print(f"  → Loaded {len(df)} hits from {Path(filepath).name}", file=sys.stderr)
        return df

    def load_forward(self, filepath: str, compressed: bool = True) -> 'BidirectionalBestHits':
        """Load forward DIAMOND results (reference -> query)."""
        self.forward_df = self.load_diamond_file(filepath, compressed)
        self._bbh_cache = None
        return self

    def load_reverse(self, filepath: str, compressed: bool = True) -> 'BidirectionalBestHits':
        """Load reverse DIAMOND results (query -> reference)."""
        self.reverse_df = self.load_diamond_file(filepath, compressed)
        self._bbh_cache = None
        return self

    def find_bbh(self,
                 min_pident: float = 30.0,
                 min_coverage: float = 50.0,
                 max_evalue: float = 1e-6) -> pd.DataFrame:
        """
        Find bidirectional best hits between reference and query.

        A BBH pair (A, B) satisfies:
        1. B is A's best hit in forward search (ref -> query)
        2. A is B's best hit in reverse search (query -> ref)

        Args:
            min_pident: Minimum percent identity threshold
            min_coverage: Minimum query coverage threshold
            max_evalue: Maximum e-value threshold

        Returns:
            DataFrame with BBH results:
                - ref_id: Reference protein/gene ID
                - query_id: Query protein/gene ID
                - pident_fwd: Percent identity (forward direction)
                - pident_rev: Percent identity (reverse direction)
                - evalue_fwd: E-value (forward)
                - evalue_rev: E-value (reverse)
                - bitscore_fwd: Bitscore (forward)
                - bitscore_rev: Bitscore (reverse)
                - avg_pident: Average percent identity
                - avg_coverage: Average coverage
                - is_bbh: Always True (for compatibility)
        """
        if self.forward_df is None or self.reverse_df is None:
            raise ValueError("Both forward and reverse DIAMOND results must be loaded")

        print(f"\nFinding bidirectional best hits...", file=sys.stderr)
        print(f"  Thresholds: pident≥{min_pident}%, coverage≥{min_coverage}%, evalue≤{max_evalue}", file=sys.stderr)

        # Filter by quality thresholds
        fwd_filtered = self.forward_df[
            (self.forward_df['pident'] >= min_pident) &
            (self.forward_df['qcovhsp'] >= min_coverage) &
            (self.forward_df['evalue'] <= max_evalue)
        ].copy()

        rev_filtered = self.reverse_df[
            (self.reverse_df['pident'] >= min_pident) &
            (self.reverse_df['qcovhsp'] >= min_coverage) &
            (self.reverse_df['evalue'] <= max_evalue)
        ].copy()

        print(f"  Forward hits after filtering: {len(fwd_filtered)}", file=sys.stderr)
        print(f"  Reverse hits after filtering: {len(rev_filtered)}", file=sys.stderr)

        if fwd_filtered.empty or rev_filtered.empty:
            print("  Warning: No hits pass quality filters", file=sys.stderr)
            return pd.DataFrame()

        # Get best hit per query in forward direction (ref -> query)
        # Using bitscore as primary criterion (more robust than evalue for ties)
        best_fwd = fwd_filtered.loc[
            fwd_filtered.groupby('qseqid')['bitscore'].idxmax()
        ][['qseqid', 'sseqid', 'pident', 'evalue', 'bitscore', 'qcovhsp', 'scovhsp']].copy()
        best_fwd.columns = ['ref_id', 'query_id', 'pident_fwd', 'evalue_fwd',
                           'bitscore_fwd', 'qcov_fwd', 'scov_fwd']

        # Get best hit per query in reverse direction (query -> ref)
        best_rev = rev_filtered.loc[
            rev_filtered.groupby('qseqid')['bitscore'].idxmax()
        ][['qseqid', 'sseqid', 'pident', 'evalue', 'bitscore', 'qcovhsp', 'scovhsp']].copy()
        best_rev.columns = ['query_id', 'ref_id', 'pident_rev', 'evalue_rev',
                           'bitscore_rev', 'qcov_rev', 'scov_rev']

        # Find reciprocal best hits (inner join on both IDs)
        bbh = pd.merge(
            best_fwd,
            best_rev,
            on=['ref_id', 'query_id'],
            how='inner'
        )

        # Calculate summary statistics
        bbh['avg_pident'] = (bbh['pident_fwd'] + bbh['pident_rev']) / 2
        bbh['avg_coverage'] = (bbh['qcov_fwd'] + bbh['scov_fwd'] +
                               bbh['qcov_rev'] + bbh['scov_rev']) / 4
        bbh['is_bbh'] = True

        # Sort by average identity
        bbh = bbh.sort_values('avg_pident', ascending=False)

        print(f"  → Found {len(bbh)} bidirectional best hits", file=sys.stderr)

        self._bbh_cache = bbh
        return bbh

    def get_one_to_one_orthologs(self,
                                  min_avg_pident: float = 90.0,
                                  min_avg_coverage: float = 90.0) -> Dict[str, str]:
        """
        Get high-confidence one-to-one ortholog pairs.

        Args:
            min_avg_pident: Minimum average percent identity
            min_avg_coverage: Minimum average coverage

        Returns:
            Dictionary mapping ref_id -> query_id for high-confidence orthologs
        """
        if self._bbh_cache is None:
            self.find_bbh()

        bbh = self._bbh_cache

        if bbh.empty:
            return {}

        high_conf = bbh[
            (bbh['avg_pident'] >= min_avg_pident) &
            (bbh['avg_coverage'] >= min_avg_coverage)
        ]

        orthologs = dict(zip(high_conf['ref_id'], high_conf['query_id']))
        print(f"  → {len(orthologs)} high-confidence orthologs (pident≥{min_avg_pident}%, cov≥{min_avg_coverage}%)",
              file=sys.stderr)

        return orthologs

    def classify_relationships(self) -> pd.DataFrame:
        """
        Classify all gene relationships based on BBH and hit patterns.

        Returns:
            DataFrame with relationship classifications:
                - ref_id, query_id: Gene IDs
                - relationship: 'bbh_ortholog', 'best_hit_only', 'multi_hit'
                - confidence: Confidence score (0-1)
        """
        if self.forward_df is None:
            raise ValueError("Forward DIAMOND results must be loaded")

        if self._bbh_cache is None:
            self.find_bbh()

        bbh_pairs = set(zip(self._bbh_cache['ref_id'], self._bbh_cache['query_id']))

        # Count hits per reference gene
        ref_hit_counts = self.forward_df.groupby('qseqid')['sseqid'].nunique()

        records = []
        for ref_id in self.forward_df['qseqid'].unique():
            ref_hits = self.forward_df[self.forward_df['qseqid'] == ref_id]
            best_hit = ref_hits.loc[ref_hits['bitscore'].idxmax()]
            query_id = best_hit['sseqid']

            if (ref_id, query_id) in bbh_pairs:
                relationship = 'bbh_ortholog'
                confidence = 1.0
            elif ref_hit_counts[ref_id] == 1:
                relationship = 'best_hit_only'
                confidence = 0.7
            else:
                relationship = 'multi_hit'
                confidence = 0.5

            records.append({
                'ref_id': ref_id,
                'query_id': query_id,
                'relationship': relationship,
                'confidence': confidence,
                'pident': best_hit['pident'],
                'coverage': best_hit['qcovhsp'],
                'hit_count': ref_hit_counts[ref_id]
            })

        return pd.DataFrame(records)

    def save_results(self, output_path: str, include_non_bbh: bool = False) -> str:
        """
        Save BBH results to TSV file.

        Args:
            output_path: Output file path
            include_non_bbh: If True, include all best hits (not just BBH)

        Returns:
            Path to saved file
        """
        if self._bbh_cache is None:
            self.find_bbh()

        output_df = self._bbh_cache.copy()

        # Select and order columns for output
        output_cols = [
            'ref_id', 'query_id',
            'pident_fwd', 'pident_rev', 'avg_pident',
            'evalue_fwd', 'evalue_rev',
            'bitscore_fwd', 'bitscore_rev',
            'qcov_fwd', 'scov_fwd', 'qcov_rev', 'scov_rev',
            'avg_coverage', 'is_bbh'
        ]

        output_df = output_df[output_cols]
        output_df.to_csv(output_path, sep='\t', index=False)

        print(f"  → Saved BBH results to {output_path}", file=sys.stderr)
        return output_path


def enrich_pavprot_with_bbh(pavprot_data: dict,
                            bbh_df: pd.DataFrame,
                            ref_col: str = 'old_transcript',
                            query_col: str = 'new_transcript') -> dict:
    """
    Enrich pavprot data dictionary with BBH information.

    This function adds BBH-related columns to pavprot entries:
        - is_bbh: Whether this pair is a bidirectional best hit
        - bbh_avg_pident: Average pident from BBH analysis
        - bbh_avg_coverage: Average coverage from BBH analysis

    Note on column mapping:
        BBH forward DIAMOND runs query→ref, so:
        - bbh_df['ref_id'] = new_transcript in pavprot
        - bbh_df['query_id'] = old_transcript in pavprot

    Args:
        pavprot_data: PAVprot data dictionary (old_gene -> list of entries)
        bbh_df: DataFrame from BidirectionalBestHits.find_bbh()
        ref_col: Column name in pavprot entries for reference ID
        query_col: Column name in pavprot entries for query ID

    Returns:
        Enriched pavprot_data dictionary
    """
    if bbh_df.empty:
        # No BBH data - mark all as non-BBH
        for entries in pavprot_data.values():
            for entry in entries:
                entry['is_bbh'] = 0
                entry['bbh_avg_pident'] = None
                entry['bbh_avg_coverage'] = None
        return pavprot_data

    # Create lookup set for fast BBH checking
    # Note: BBH ref_id = pavprot new_transcript, BBH query_id = pavprot old_transcript
    # So we key by (new_transcript, old_transcript) to match (ref_id, query_id)
    bbh_lookup = {}
    for _, row in bbh_df.iterrows():
        # Key: (pavprot_new_transcript, pavprot_old_transcript)
        key = (row['ref_id'], row['query_id'])
        bbh_lookup[key] = {
            'avg_pident': row['avg_pident'],
            'avg_coverage': row['avg_coverage']
        }

    # Enrich entries
    bbh_count = 0
    for entries in pavprot_data.values():
        for entry in entries:
            ref_id = entry.get(ref_col, '')
            query_id = entry.get(query_col, '')

            # Match pavprot (new_transcript, old_transcript) to BBH (ref_id, query_id)
            key = (query_id, ref_id)
            if key in bbh_lookup:
                entry['is_bbh'] = 1
                entry['bbh_avg_pident'] = bbh_lookup[key]['avg_pident']
                entry['bbh_avg_coverage'] = bbh_lookup[key]['avg_coverage']
                bbh_count += 1
            else:
                entry['is_bbh'] = 0
                entry['bbh_avg_pident'] = None
                entry['bbh_avg_coverage'] = None

    print(f"  → Enriched {bbh_count} entries with BBH information", file=sys.stderr)
    return pavprot_data


def create_argument_parser() -> argparse.ArgumentParser:
    """Create argument parser for standalone usage."""
    parser = argparse.ArgumentParser(
        description="Bidirectional Best Hit (BBH) Analysis for Ortholog Identification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic BBH analysis with two DIAMOND files
    python bidirectional_best_hits.py \\
        --fwd ref_vs_query_diamond.tsv.gz \\
        --rev query_vs_ref_diamond.tsv.gz \\
        --output bbh_results.tsv

    # With custom thresholds
    python bidirectional_best_hits.py \\
        --fwd ref_vs_query.tsv.gz \\
        --rev query_vs_ref.tsv.gz \\
        --min-pident 90 \\
        --min-coverage 90 \\
        --output high_conf_orthologs.tsv
        """
    )

    parser.add_argument('--fwd', required=True,
                        help='Forward DIAMOND results (ref -> query)')
    parser.add_argument('--rev', required=True,
                        help='Reverse DIAMOND results (query -> ref)')
    parser.add_argument('--output', '-o', default='bbh_results.tsv',
                        help='Output file path (default: bbh_results.tsv)')
    parser.add_argument('--min-pident', type=float, default=30.0,
                        help='Minimum percent identity (default: 30.0)')
    parser.add_argument('--min-coverage', type=float, default=50.0,
                        help='Minimum query coverage (default: 50.0)')
    parser.add_argument('--max-evalue', type=float, default=1e-6,
                        help='Maximum e-value (default: 1e-6)')
    parser.add_argument('--high-conf-pident', type=float, default=90.0,
                        help='Pident threshold for high-confidence orthologs (default: 90.0)')
    parser.add_argument('--high-conf-coverage', type=float, default=90.0,
                        help='Coverage threshold for high-confidence orthologs (default: 90.0)')

    return parser


def main():
    """Main entry point for standalone BBH analysis."""
    parser = create_argument_parser()
    args = parser.parse_args()

    print("="*70, file=sys.stderr)
    print("Bidirectional Best Hit (BBH) Analysis", file=sys.stderr)
    print("="*70, file=sys.stderr)

    # Initialize analyzer
    bbh = BidirectionalBestHits()

    # Load DIAMOND results
    print(f"\nLoading DIAMOND results...", file=sys.stderr)
    bbh.load_forward(args.fwd)
    bbh.load_reverse(args.rev)

    # Find BBH pairs
    bbh_df = bbh.find_bbh(
        min_pident=args.min_pident,
        min_coverage=args.min_coverage,
        max_evalue=args.max_evalue
    )

    if not bbh_df.empty:
        # Get high-confidence orthologs
        orthologs = bbh.get_one_to_one_orthologs(
            min_avg_pident=args.high_conf_pident,
            min_avg_coverage=args.high_conf_coverage
        )

        # Save results
        bbh.save_results(args.output)

        # Print summary
        print(f"\n" + "="*70, file=sys.stderr)
        print(f"Summary:", file=sys.stderr)
        print(f"  Total BBH pairs: {len(bbh_df)}", file=sys.stderr)
        print(f"  High-confidence orthologs: {len(orthologs)}", file=sys.stderr)
        print(f"  Average pident: {bbh_df['avg_pident'].mean():.1f}%", file=sys.stderr)
        print(f"  Average coverage: {bbh_df['avg_coverage'].mean():.1f}%", file=sys.stderr)
        print("="*70, file=sys.stderr)
    else:
        print("\nNo BBH pairs found with current thresholds.", file=sys.stderr)
        print("Try lowering --min-pident or --min-coverage.", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
