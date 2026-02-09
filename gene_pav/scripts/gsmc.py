#!/usr/bin/env python3
"""
Detect Advanced Gene Mapping Scenarios

This module implements detection for EXCLUSIVE gene mapping scenarios.
Each gene pair belongs to exactly one scenario - there is no overlap.

Scenarios (mutually exclusive):
- Scenario E: 1:1 orthologs (ref→1 query AND query→1 ref)
- Scenario A: 1:2N mappings (ref→exactly 2 queries, NOT in CDI)
- Scenario J: 1:2N+ mappings (ref→3+ queries, NOT in CDI)
- Scenario B: N:1 mappings (query→2+ refs, NOT in CDI)
- Scenario CDI: Cross-mapping (both sides have multiple mappings)
- Scenario F: Positional swaps [DISABLED - not applicable to current data]
- Scenarios G, H: Unmapped genes

Exclusivity Rules:
1. CDI takes priority over A, B, J
2. A = exactly 2 queries (1:2N)
3. J = 3+ queries (1:2N+)
4. E is exclusive by definition
5. G, H are genes NOT in pavprot output

Usage:
    python gsmc.py \
        --pavprot-output pavprot_out/synonym_mapping_liftover_gffcomp.tsv \
        --ref-faa ref.faa \
        --qry-faa query.faa \
        --gff ref.gff,query.gff \
        --scenarios E,A,B,J,CDI,G,H
"""

import argparse
import os
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
import pandas as pd
from pathlib import Path


# =============================================================================
# Transcript Aggregation Helpers
# =============================================================================

def build_transcript_lookup(pavprot_df: pd.DataFrame) -> Tuple[Dict, Dict]:
    """
    Build lookup dictionaries for transcripts per gene.

    Returns:
        Tuple of (old_gene_transcripts, new_gene_transcripts)
        Each dict maps gene_id -> (transcript_list, transcript_count)
    """
    ref_tx = pavprot_df.groupby('old_gene')['old_transcript'].agg(
        lambda x: (list(x.unique()), len(x.unique()))
    ).to_dict()

    query_tx = pavprot_df.groupby('new_gene')['new_transcript'].agg(
        lambda x: (list(x.unique()), len(x.unique()))
    ).to_dict()

    return ref_tx, query_tx


def has_pairwise_columns(pavprot_df: pd.DataFrame) -> bool:
    """Check if pavprot output has pairwise alignment columns."""
    pairwise_cols = ['pairwise_identity', 'pairwise_coverage_old',
                     'pairwise_coverage_new', 'pairwise_aligned_length']
    return all(col in pavprot_df.columns for col in pairwise_cols)


def aggregate_pairwise_metrics(
    pavprot_df: pd.DataFrame,
    old_gene: str,
    new_gene: str
) -> Dict:
    """
    Aggregate pairwise alignment metrics for a gene pair.

    Returns dict with:
    - avg_* columns: mean values across transcripts
    - *_all columns: comma-separated values for each transcript pair

    Args:
        pavprot_df: DataFrame from pavprot output with pairwise columns
        old_gene: Reference gene ID
        new_gene: Query gene ID

    Returns:
        Dict with aggregated pairwise metrics
    """
    # Filter to this gene pair
    mask = (pavprot_df['old_gene'] == old_gene) & (pavprot_df['new_gene'] == new_gene)
    subset = pavprot_df[mask]

    if len(subset) == 0:
        return {
            'avg_pairwise_identity': None,
            'avg_pairwise_coverage_old': None,
            'avg_pairwise_coverage_new': None,
            'avg_pairwise_aligned_length': None,
            'pairwise_identity_all': '',
            'pairwise_coverage_old_all': '',
            'pairwise_coverage_new_all': '',
            'pairwise_aligned_length_all': '',
        }

    # Get non-NA values for averaging
    identity_vals = subset['pairwise_identity'].dropna().tolist()
    cov_ref_vals = subset['pairwise_coverage_old'].dropna().tolist()
    cov_query_vals = subset['pairwise_coverage_new'].dropna().tolist()
    aligned_len_vals = subset['pairwise_aligned_length'].dropna().tolist()

    # Calculate averages
    avg_identity = sum(identity_vals) / len(identity_vals) if identity_vals else None
    avg_cov_ref = sum(cov_ref_vals) / len(cov_ref_vals) if cov_ref_vals else None
    avg_cov_query = sum(cov_query_vals) / len(cov_query_vals) if cov_query_vals else None
    avg_aligned_len = sum(aligned_len_vals) / len(aligned_len_vals) if aligned_len_vals else None

    # Create comma-separated strings
    identity_all = ','.join(f"{v:.2f}" for v in identity_vals) if identity_vals else ''
    cov_ref_all = ','.join(f"{v:.2f}" for v in cov_ref_vals) if cov_ref_vals else ''
    cov_query_all = ','.join(f"{v:.2f}" for v in cov_query_vals) if cov_query_vals else ''
    aligned_len_all = ','.join(str(int(v)) for v in aligned_len_vals) if aligned_len_vals else ''

    return {
        'avg_pairwise_identity': avg_identity,
        'avg_pairwise_coverage_old': avg_cov_ref,
        'avg_pairwise_coverage_new': avg_cov_query,
        'avg_pairwise_aligned_length': avg_aligned_len,
        'pairwise_identity_all': identity_all,
        'pairwise_coverage_old_all': cov_ref_all,
        'pairwise_coverage_new_all': cov_query_all,
        'pairwise_aligned_length_all': aligned_len_all,
    }




def parse_gff_transcripts(gff_path: str) -> Dict[str, Tuple[List[str], int]]:
    """
    Parse GFF3 file to extract transcripts per gene.

    Returns:
        Dict mapping gene_id -> (transcript_list, transcript_count)
    """
    gene_transcripts = defaultdict(set)

    # Feature types for transcripts
    transcript_types = {'mRNA', 'transcript', 'ncRNA', 'tRNA', 'rRNA'}

    with open(gff_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            cols = line.split('\t')
            if len(cols) < 9:
                continue

            feature_type = cols[2]
            if feature_type not in transcript_types:
                continue

            attrs = cols[8]
            transcript_id = None
            parent_gene = None

            for pair in attrs.split(';'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    if k == 'ID':
                        transcript_id = v
                    elif k == 'Parent':
                        parent_gene = v

            if transcript_id and parent_gene:
                gene_transcripts[parent_gene].add(transcript_id)

    # Convert to (list, count) format
    return {g: (sorted(list(tx)), len(tx)) for g, tx in gene_transcripts.items()}


# =============================================================================
# CDI Gene Detection Helper (for exclusivity)
# =============================================================================

def get_cdi_genes(pavprot_df: pd.DataFrame) -> Tuple[Set[str], Set[str]]:
    """
    Get genes that belong to CDI (cross-mapping) scenario.

    CDI genes are those where:
    - old_gene maps to multiple query genes AND
    - at least one of those query genes maps to multiple ref genes

    This is used to exclude CDI genes from A, B, J scenarios.

    Args:
        pavprot_df: DataFrame from pavprot output

    Returns:
        Tuple of (cdi_old_genes, cdi_new_genes)
    """
    # Get unique gene pairs
    gene_pairs = pavprot_df[['old_gene', 'new_gene']].drop_duplicates()

    # Count mappings per gene
    ref_counts = gene_pairs.groupby('old_gene')['new_gene'].nunique()
    query_counts = gene_pairs.groupby('new_gene')['old_gene'].nunique()

    # Find multi-mapping genes
    refs_multi = set(ref_counts[ref_counts > 1].index)
    queries_multi = set(query_counts[query_counts > 1].index)

    # CDI: pairs where BOTH sides are multi-mapping
    cdi_old_genes = set()
    cdi_new_genes = set()

    for _, row in gene_pairs.iterrows():
        old_gene = row['old_gene']
        new_gene = row['new_gene']

        # Check if this pair is in CDI
        if old_gene in refs_multi and new_gene in queries_multi:
            cdi_old_genes.add(old_gene)
            cdi_new_genes.add(new_gene)

    return cdi_old_genes, cdi_new_genes


# =============================================================================
# Scenario E: 1:1 Orthologs
# =============================================================================

def detect_one_to_one_orthologs(pavprot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect Scenario E: 1:1 ortholog pairs (exclusive mappings).

    A 1:1 ortholog pair is where:
    - The ref gene maps to exactly one query gene
    - That query gene maps to exactly one ref gene

    Args:
        pavprot_df: DataFrame from pavprot output

    Returns:
        DataFrame with 1:1 ortholog pairs and transcript info
    """
    # Get unique gene pairs
    gene_pairs = pavprot_df[['old_gene', 'new_gene']].drop_duplicates()

    # Count mappings per gene
    ref_counts = gene_pairs.groupby('old_gene')['new_gene'].nunique()
    query_counts = gene_pairs.groupby('new_gene')['old_gene'].nunique()

    # Find genes with exactly 1 mapping
    refs_1to1 = set(ref_counts[ref_counts == 1].index)
    queries_1to1 = set(query_counts[query_counts == 1].index)

    # True 1:1 pairs: both conditions met
    one_to_one = gene_pairs[
        (gene_pairs['old_gene'].isin(refs_1to1)) &
        (gene_pairs['new_gene'].isin(queries_1to1))
    ]

    print(f"  Found {len(one_to_one)} 1:1 ortholog pairs")

    if len(one_to_one) == 0:
        return pd.DataFrame()

    # Build transcript lookup
    ref_tx_lookup, query_tx_lookup = build_transcript_lookup(pavprot_df)

    # Check if pairwise columns exist
    include_pairwise = has_pairwise_columns(pavprot_df)

    # Create output with transcript info
    results = []
    for _, row in one_to_one.iterrows():
        old_gene = row['old_gene']
        new_gene = row['new_gene']

        ref_tx_list, ref_tx_count = ref_tx_lookup.get(old_gene, ([], 0))
        query_tx_list, query_tx_count = query_tx_lookup.get(new_gene, ([], 0))

        result_row = {
            'old_gene': old_gene,
            'old_transcripts': ';'.join(ref_tx_list) if ref_tx_list else '',
            'old_transcript_count': ref_tx_count,
            'new_gene': new_gene,
            'new_transcripts': ';'.join(query_tx_list) if query_tx_list else '',
            'new_transcript_count': query_tx_count,
            'scenario': 'E',
            'mapping_type': '1to1'
        }

        # Add pairwise metrics if available
        if include_pairwise:
            pairwise_metrics = aggregate_pairwise_metrics(pavprot_df, old_gene, new_gene)
            result_row.update(pairwise_metrics)

        results.append(result_row)

    return pd.DataFrame(results)


# =============================================================================
# Scenario A: 1:2N Mappings (One ref -> Exactly 2 queries, NOT in CDI)
# =============================================================================

def detect_one_to_many(
    pavprot_df: pd.DataFrame,
    exclude_refs: Optional[Set[str]] = None
) -> pd.DataFrame:
    """
    Detect Scenario A: 1:2N mappings where one ref gene maps to EXACTLY 2 query genes.

    EXCLUSIVE scenario - excludes genes that are in CDI (cross-mapping).

    Args:
        pavprot_df: DataFrame from pavprot output
        exclude_refs: Set of ref genes to exclude (CDI genes)

    Returns:
        DataFrame with 1:2N mappings and transcript info
    """
    exclude_refs = exclude_refs or set()

    # Get unique gene pairs
    gene_pairs = pavprot_df[['old_gene', 'new_gene']].drop_duplicates()

    # Count mappings per ref gene
    ref_counts = gene_pairs.groupby('old_gene')['new_gene'].nunique()

    # Find ref genes with EXACTLY 2 query mappings (not >1)
    refs_1to2N = set(ref_counts[ref_counts == 2].index)

    # Exclude CDI genes to maintain mutual exclusivity
    refs_1to2N = refs_1to2N - exclude_refs

    # Get all pairs for these ref genes
    one_to_many = gene_pairs[gene_pairs['old_gene'].isin(refs_1to2N)]

    print(f"  Found {len(refs_1to2N)} ref genes with 1:2N mappings ({len(one_to_many)} total pairs)")
    if exclude_refs:
        print(f"    (excluded {len(exclude_refs)} CDI genes)")

    if len(one_to_many) == 0:
        return pd.DataFrame()

    # Build transcript lookup
    ref_tx_lookup, query_tx_lookup = build_transcript_lookup(pavprot_df)

    # Check if pairwise columns exist
    include_pairwise = has_pairwise_columns(pavprot_df)

    # Create output with transcript info, grouped by ref gene
    results = []
    for old_gene in sorted(refs_1to2N):
        new_genes = sorted(gene_pairs[gene_pairs['old_gene'] == old_gene]['new_gene'].tolist())
        ref_tx_list, ref_tx_count = ref_tx_lookup.get(old_gene, ([], 0))

        for new_gene in new_genes:
            query_tx_list, query_tx_count = query_tx_lookup.get(new_gene, ([], 0))

            result_row = {
                'old_gene': old_gene,
                'old_transcripts': ';'.join(ref_tx_list) if ref_tx_list else '',
                'old_transcript_count': ref_tx_count,
                'new_gene': new_gene,
                'new_transcripts': ';'.join(query_tx_list) if query_tx_list else '',
                'new_transcript_count': query_tx_count,
                'query_count': len(new_genes),
                'all_new_genes': ';'.join(new_genes),
                'scenario': 'A',
                'mapping_type': '1to2N'
            }

            # Add pairwise metrics if available
            if include_pairwise:
                pairwise_metrics = aggregate_pairwise_metrics(pavprot_df, old_gene, new_gene)
                result_row.update(pairwise_metrics)

            results.append(result_row)

    return pd.DataFrame(results)


# =============================================================================
# Scenario B: N:1 Mappings (Multiple refs -> One query, NOT in CDI)
# =============================================================================

def detect_many_to_one(
    pavprot_df: pd.DataFrame,
    exclude_queries: Optional[Set[str]] = None
) -> pd.DataFrame:
    """
    Detect Scenario B: N:1 mappings where multiple ref genes map to one query gene.

    EXCLUSIVE scenario - excludes genes that are in CDI (cross-mapping).

    Args:
        pavprot_df: DataFrame from pavprot output
        exclude_queries: Set of query genes to exclude (CDI genes)

    Returns:
        DataFrame with N:1 mappings and transcript info
    """
    exclude_queries = exclude_queries or set()

    # Get unique gene pairs
    gene_pairs = pavprot_df[['old_gene', 'new_gene']].drop_duplicates()

    # Count mappings per query gene
    query_counts = gene_pairs.groupby('new_gene')['old_gene'].nunique()

    # Find query genes with >1 ref mapping
    queries_Nto1 = set(query_counts[query_counts > 1].index)

    # Exclude CDI genes to maintain mutual exclusivity
    queries_Nto1 = queries_Nto1 - exclude_queries

    # Get all pairs for these query genes
    many_to_one = gene_pairs[gene_pairs['new_gene'].isin(queries_Nto1)]

    print(f"  Found {len(queries_Nto1)} query genes with N:1 mappings ({len(many_to_one)} total pairs)")
    if exclude_queries:
        print(f"    (excluded {len(exclude_queries)} CDI genes)")

    if len(many_to_one) == 0:
        return pd.DataFrame()

    # Build transcript lookup
    ref_tx_lookup, query_tx_lookup = build_transcript_lookup(pavprot_df)

    # Check if pairwise columns exist
    include_pairwise = has_pairwise_columns(pavprot_df)

    # Create output with transcript info, grouped by query gene
    results = []
    for new_gene in sorted(queries_Nto1):
        old_genes = sorted(gene_pairs[gene_pairs['new_gene'] == new_gene]['old_gene'].tolist())
        query_tx_list, query_tx_count = query_tx_lookup.get(new_gene, ([], 0))

        for old_gene in old_genes:
            ref_tx_list, ref_tx_count = ref_tx_lookup.get(old_gene, ([], 0))

            result_row = {
                'old_gene': old_gene,
                'old_transcripts': ';'.join(ref_tx_list) if ref_tx_list else '',
                'old_transcript_count': ref_tx_count,
                'new_gene': new_gene,
                'new_transcripts': ';'.join(query_tx_list) if query_tx_list else '',
                'new_transcript_count': query_tx_count,
                'ref_count': len(old_genes),
                'all_old_genes': ';'.join(old_genes),
                'scenario': 'B',
                'mapping_type': 'Nto1'
            }

            # Add pairwise metrics if available
            if include_pairwise:
                pairwise_metrics = aggregate_pairwise_metrics(pavprot_df, old_gene, new_gene)
                result_row.update(pairwise_metrics)

            results.append(result_row)

    return pd.DataFrame(results)


# =============================================================================
# Scenario J: 1:2N+ Mappings (One ref -> 3+ queries, NOT in CDI)
# =============================================================================

def detect_complex_one_to_many(
    pavprot_df: pd.DataFrame,
    min_count: int = 3,
    exclude_refs: Optional[Set[str]] = None
) -> pd.DataFrame:
    """
    Detect Scenario J: 1:2N+ mappings where one ref gene maps to 3+ query genes.

    EXCLUSIVE scenario - excludes genes that are in CDI (cross-mapping).

    Args:
        pavprot_df: DataFrame from pavprot output
        min_count: Minimum number of query genes to qualify (default: 3)
        exclude_refs: Set of ref genes to exclude (CDI genes)

    Returns:
        DataFrame with 1:2N+ mappings and transcript info
    """
    exclude_refs = exclude_refs or set()

    # Get unique gene pairs
    gene_pairs = pavprot_df[['old_gene', 'new_gene']].drop_duplicates()

    # Count mappings per ref gene
    ref_counts = gene_pairs.groupby('old_gene')['new_gene'].nunique()

    # Find ref genes with >= min_count query mappings
    refs_complex = set(ref_counts[ref_counts >= min_count].index)

    # Exclude CDI genes to maintain mutual exclusivity
    refs_complex = refs_complex - exclude_refs

    # Get all pairs for these ref genes
    complex_mappings = gene_pairs[gene_pairs['old_gene'].isin(refs_complex)]

    print(f"  Found {len(refs_complex)} ref genes with 1:2N+ mappings ({len(complex_mappings)} total pairs)")
    if exclude_refs:
        print(f"    (excluded {len(exclude_refs)} CDI genes)")

    if len(complex_mappings) == 0:
        return pd.DataFrame()

    # Build transcript lookup
    ref_tx_lookup, query_tx_lookup = build_transcript_lookup(pavprot_df)

    # Check if pairwise columns exist
    include_pairwise = has_pairwise_columns(pavprot_df)

    # Create output with transcript info, grouped by ref gene
    results = []
    for old_gene in sorted(refs_complex):
        new_genes = sorted(gene_pairs[gene_pairs['old_gene'] == old_gene]['new_gene'].tolist())
        ref_tx_list, ref_tx_count = ref_tx_lookup.get(old_gene, ([], 0))

        for new_gene in new_genes:
            query_tx_list, query_tx_count = query_tx_lookup.get(new_gene, ([], 0))

            result_row = {
                'old_gene': old_gene,
                'old_transcripts': ';'.join(ref_tx_list) if ref_tx_list else '',
                'old_transcript_count': ref_tx_count,
                'new_gene': new_gene,
                'new_transcripts': ';'.join(query_tx_list) if query_tx_list else '',
                'new_transcript_count': query_tx_count,
                'query_count': len(new_genes),
                'all_new_genes': ';'.join(new_genes),
                'scenario': 'J',
                'mapping_type': '1to2N+'
            }

            # Add pairwise metrics if available
            if include_pairwise:
                pairwise_metrics = aggregate_pairwise_metrics(pavprot_df, old_gene, new_gene)
                result_row.update(pairwise_metrics)

            results.append(result_row)

    return pd.DataFrame(results)


# =============================================================================
# Scenarios C, D, I: Cross-Mapping Classification
# =============================================================================

def classify_cross_mappings(pavprot_df: pd.DataFrame) -> pd.DataFrame:
    """
    Distinguish Scenarios C, D, I from cross-mapping groups.

    Scenario C: One ref maps to both queries, other ref maps to one
    Scenario D: Both refs map to both queries (full cross)
    Scenario I: One ref maps to one query, other ref maps to both

    Args:
        pavprot_df: DataFrame from pavprot output

    Returns:
        DataFrame with cross_mapping_type and cross_mapping_group_id columns
    """
    # Find entries where both flags indicate cross-mapping
    cross_mask = (pavprot_df['old_multi_new'] >= 1) & (pavprot_df['new_multi_old'] >= 1)

    if not cross_mask.any():
        print("  No cross-mapping patterns found")
        return pd.DataFrame()

    cross_df = pavprot_df[cross_mask].copy()

    # Build mapping: old_gene -> set of new_genes
    ref_to_queries = defaultdict(set)
    query_to_refs = defaultdict(set)

    for _, row in cross_df.iterrows():
        old_gene = row['old_gene']
        new_gene = row['new_gene']
        ref_to_queries[old_gene].add(new_gene)
        query_to_refs[new_gene].add(old_gene)

    # Build connected components (cross-mapping groups)
    def find_connected_component(start_ref: str, ref_to_q: dict, q_to_ref: dict) -> Tuple[Set[str], Set[str]]:
        """Find all connected ref and query genes starting from a ref gene."""
        visited_refs = set()
        visited_queries = set()
        stack = [start_ref]

        while stack:
            current = stack.pop()
            if current in visited_refs:
                continue
            visited_refs.add(current)

            for q in ref_to_q.get(current, []):
                if q not in visited_queries:
                    visited_queries.add(q)
                    for r in q_to_ref.get(q, []):
                        if r not in visited_refs:
                            stack.append(r)

        return visited_refs, visited_queries

    # Find all groups
    all_refs = set(ref_to_queries.keys())
    processed_refs = set()
    groups = []

    for ref in all_refs:
        if ref in processed_refs:
            continue
        ref_set, query_set = find_connected_component(ref, ref_to_queries, query_to_refs)
        processed_refs.update(ref_set)
        groups.append((ref_set, query_set))

    # Build transcript lookup
    ref_tx_lookup, query_tx_lookup = build_transcript_lookup(pavprot_df)

    # Check if pairwise columns exist
    include_pairwise = has_pairwise_columns(pavprot_df)

    # Classify each group
    results = []

    for group_id, (ref_set, query_set) in enumerate(groups):
        # Build mapping matrix for this group
        ref_list = sorted(ref_set)
        query_list = sorted(query_set)

        # Count how many queries each ref maps to
        ref_mapping_counts = {r: len(ref_to_queries[r] & query_set) for r in ref_list}

        # Classify based on mapping pattern
        if len(ref_list) == 2 and len(query_list) == 2:
            r1, r2 = ref_list
            c1, c2 = ref_mapping_counts[r1], ref_mapping_counts[r2]

            if c1 == 2 and c2 == 2:
                cross_type = 'full_D'
            elif c1 == 2 and c2 == 1:
                cross_type = 'partial_C'
            elif c1 == 1 and c2 == 2:
                cross_type = 'partial_I'
            else:
                cross_type = 'other'
        else:
            # Larger groups - classify as complex
            cross_type = 'complex'

        # Add result for each gene pair in this group
        for ref in ref_list:
            for query in query_list:
                if query in ref_to_queries[ref]:
                    # Get transcript info
                    ref_tx_list, ref_tx_count = ref_tx_lookup.get(ref, ([], 0))
                    query_tx_list, query_tx_count = query_tx_lookup.get(query, ([], 0))

                    result_row = {
                        'old_gene': ref,
                        'old_transcripts': ';'.join(ref_tx_list) if ref_tx_list else '',
                        'old_transcript_count': ref_tx_count,
                        'new_gene': query,
                        'new_transcripts': ';'.join(query_tx_list) if query_tx_list else '',
                        'new_transcript_count': query_tx_count,
                        'scenario': 'CDI',
                        'mapping_type': 'complex',
                        'cross_mapping_type': cross_type,
                        'cross_mapping_group_id': group_id,
                        'group_ref_count': len(ref_list),
                        'group_query_count': len(query_list),
                        'old_genes_in_group': ';'.join(ref_list),
                        'new_genes_in_group': ';'.join(query_list)
                    }

                    # Add pairwise metrics if available
                    if include_pairwise:
                        pairwise_metrics = aggregate_pairwise_metrics(pavprot_df, ref, query)
                        result_row.update(pairwise_metrics)

                    results.append(result_row)

    result_df = pd.DataFrame(results)

    # Count by type
    if len(result_df) > 0:
        type_counts = result_df.groupby('cross_mapping_type')['cross_mapping_group_id'].nunique()
        print(f"  Cross-mapping classification:")
        for ctype, count in type_counts.items():
            print(f"    {ctype}: {count} groups")

    return result_df


# =============================================================================
# Scenario F: Positional Swaps [DISABLED]
# =============================================================================
#
# TODO: Scenario F is DISABLED (2026-01-09)
# Reason: Analysis found 100% overlap between F and E scenarios.
# Positional swap detection requires more robust synteny analysis to be
# meaningful for the current dataset. Kept as TODO for future implementation.
#
# To re-enable:
# 1. Uncomment the functions below
# 2. Add 'F' back to the default scenarios list
# 3. Implement proper synteny-based swap detection to avoid E overlap
# =============================================================================


def parse_gff_positions(gff_path: str) -> Dict[str, Tuple[str, int, int, str]]:
    """
    Parse GFF3 file to extract gene positions.

    Returns:
        Dict mapping gene_id to (chrom, start, end, strand)
    """
    positions = {}

    # Gene feature types in different GFF formats
    gene_types = {'gene', 'protein_coding_gene', 'pseudogene', 'ncRNA_gene'}

    with open(gff_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            cols = line.split('\t')
            if len(cols) < 9:
                continue

            feature_type = cols[2]
            if feature_type not in gene_types:
                continue

            chrom = cols[0]
            start = int(cols[3])
            end = int(cols[4])
            strand = cols[6]

            # Parse attributes to get gene ID
            attrs = cols[8]
            gene_id = None
            for pair in attrs.split(';'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    if k == 'ID':
                        gene_id = v
                        break

            if gene_id:
                positions[gene_id] = (chrom, start, end, strand)

    return positions


def build_adjacency_map(positions: Dict[str, Tuple[str, int, int, str]], gene_set: Set[str]) -> Dict[str, str]:
    """
    Build a map of adjacent genes (gene -> next gene in genomic order).

    Only considers genes that are in gene_set (i.e., have orthologs).

    Args:
        positions: Dict mapping gene_id to (chrom, start, end, strand)
        gene_set: Set of genes to consider (those with orthologs)

    Returns:
        Dict mapping each gene to its next adjacent gene (in gene_set)
    """
    # Group genes by chromosome
    chrom_genes = defaultdict(list)
    for gene_id, (chrom, start, end, strand) in positions.items():
        if gene_id in gene_set:
            chrom_genes[chrom].append((start, gene_id))

    # Sort each chromosome by position and build adjacency
    adjacency = {}
    for chrom, genes in chrom_genes.items():
        sorted_genes = sorted(genes, key=lambda x: x[0])
        for i in range(len(sorted_genes) - 1):
            gene_a = sorted_genes[i][1]
            gene_b = sorted_genes[i + 1][1]
            adjacency[gene_a] = gene_b

    return adjacency


def detect_positional_swaps(
    pavprot_df: pd.DataFrame,
    ref_gff: str,
    query_gff: str,
    max_distance: int = 100000
) -> pd.DataFrame:
    """
    Detect Scenario F: Positional swaps where adjacent genes have inverted order.

    Only detects swaps between genes that are truly adjacent (consecutive) in
    the reference genome. A swap is reported when two adjacent ref genes map
    to query genes that appear in reversed order.

    Args:
        pavprot_df: DataFrame from pavprot output
        ref_gff: Path to reference GFF3
        query_gff: Path to query GFF3
        max_distance: Maximum distance between genes (for reporting, not filtering)

    Returns:
        DataFrame of detected positional swaps
    """
    # Parse gene positions
    print(f"  Parsing reference GFF: {ref_gff}")
    ref_positions = parse_gff_positions(ref_gff)
    print(f"    Found {len(ref_positions)} gene positions")

    print(f"  Parsing query GFF: {query_gff}")
    query_positions = parse_gff_positions(query_gff)
    print(f"    Found {len(query_positions)} gene positions")

    # Get 1:1 mappings only (exclusive orthologs)
    orthologs = pavprot_df[
        (pavprot_df['old_multi_new'] == 0) &
        (pavprot_df['new_multi_old'] == 0)
    ][['old_gene', 'new_gene']].drop_duplicates()

    print(f"  Analyzing {len(orthologs)} 1:1 ortholog pairs")

    # Build lookups
    ref_to_query = dict(zip(orthologs['old_gene'], orthologs['new_gene']))
    query_to_ref = dict(zip(orthologs['new_gene'], orthologs['old_gene']))

    # Get sets of genes with orthologs
    old_genes_with_orthologs = set(ref_to_query.keys())
    new_genes_with_orthologs = set(query_to_ref.keys())

    # Build adjacency maps (only for genes with orthologs)
    print(f"  Building adjacency maps for orthologous genes...")
    ref_adjacency = build_adjacency_map(ref_positions, old_genes_with_orthologs)
    print(f"    Reference: {len(ref_adjacency)} adjacent pairs")

    # Build transcript lookup
    ref_tx_lookup, query_tx_lookup = build_transcript_lookup(pavprot_df)

    # Find swaps: adjacent in ref but order inverted in query
    swaps = []

    for ref_a, ref_b in ref_adjacency.items():
        # Get corresponding query genes
        query_a = ref_to_query.get(ref_a)
        query_b = ref_to_query.get(ref_b)

        if not query_a or not query_b:
            continue

        # Check positions exist
        if ref_a not in ref_positions or ref_b not in ref_positions:
            continue
        if query_a not in query_positions or query_b not in query_positions:
            continue

        ref_a_pos = ref_positions[ref_a]
        ref_b_pos = ref_positions[ref_b]
        query_a_pos = query_positions[query_a]
        query_b_pos = query_positions[query_b]

        # Must be on same chromosome in query to detect swap
        if query_a_pos[0] != query_b_pos[0]:
            continue

        # In reference, ref_a comes before ref_b (by adjacency definition)
        # Check if order is inverted in query
        query_a_before_b = query_a_pos[1] < query_b_pos[1]

        # Swap detected if query order is inverted (ref_a maps to query gene that comes AFTER)
        if not query_a_before_b:
            ref_distance = abs(ref_b_pos[1] - ref_a_pos[1])
            query_distance = abs(query_b_pos[1] - query_a_pos[1])

            # Get transcript info for all 4 genes
            ref_a_tx, ref_a_tx_count = ref_tx_lookup.get(ref_a, ([], 0))
            ref_b_tx, ref_b_tx_count = ref_tx_lookup.get(ref_b, ([], 0))
            query_a_tx, query_a_tx_count = query_tx_lookup.get(query_a, ([], 0))
            query_b_tx, query_b_tx_count = query_tx_lookup.get(query_b, ([], 0))

            swaps.append({
                'old_gene_1': ref_a,
                'old_gene_1_transcripts': ';'.join(ref_a_tx) if ref_a_tx else '',
                'old_gene_1_tx_count': ref_a_tx_count,
                'old_gene_2': ref_b,
                'old_gene_2_transcripts': ';'.join(ref_b_tx) if ref_b_tx else '',
                'old_gene_2_tx_count': ref_b_tx_count,
                'new_gene_1': query_a,
                'new_gene_1_transcripts': ';'.join(query_a_tx) if query_a_tx else '',
                'new_gene_1_tx_count': query_a_tx_count,
                'new_gene_2': query_b,
                'new_gene_2_transcripts': ';'.join(query_b_tx) if query_b_tx else '',
                'new_gene_2_tx_count': query_b_tx_count,
                'ref_chrom': ref_a_pos[0],
                'old_gene_1_start': ref_a_pos[1],
                'old_gene_2_start': ref_b_pos[1],
                'query_chrom': query_a_pos[0],
                'new_gene_1_start': query_a_pos[1],
                'new_gene_2_start': query_b_pos[1],
                'ref_distance': ref_distance,
                'query_distance': query_distance,
                'swap_type': 'adjacent_order_inversion'
            })

    result_df = pd.DataFrame(swaps)
    print(f"  Found {len(result_df)} adjacent positional swaps")

    return result_df


# =============================================================================
# Scenarios G, H: Unmapped Genes
# =============================================================================

def parse_fasta_ids(fasta_path: str, is_query: bool = False) -> Set[str]:
    """
    Parse FASTA file to extract protein/gene IDs.

    Args:
        fasta_path: Path to FASTA file
        is_query: If True, handle query ID format

    Returns:
        Set of gene/protein IDs
    """
    ids = set()

    with open(fasta_path) as f:
        for line in f:
            if line.startswith('>'):
                header = line[1:].strip()
                protein_id = header.split()[0].split('|')[0]

                # For query, extract gene ID from transcript ID
                if is_query:
                    # Handle format like FOZG_00001-t36_1 -> FOZG_00001
                    if '-t' in protein_id:
                        gene_id = protein_id.rsplit('-t', 1)[0]
                        ids.add(gene_id)
                    else:
                        ids.add(protein_id)
                else:
                    ids.add(protein_id)

    return ids


def parse_gff_gene_ids(gff_path: str) -> Set[str]:
    """
    Parse GFF3 file to extract all gene IDs.

    Args:
        gff_path: Path to GFF3 file

    Returns:
        Set of gene IDs
    """
    gene_ids = set()

    # Gene feature types in different GFF formats
    gene_types = {'gene', 'protein_coding_gene', 'pseudogene', 'ncRNA_gene'}

    with open(gff_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            cols = line.split('\t')
            if len(cols) < 9:
                continue

            feature_type = cols[2]
            if feature_type not in gene_types:
                continue

            attrs = cols[8]
            for pair in attrs.split(';'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    if k == 'ID':
                        gene_ids.add(v)
                        break

    return gene_ids


def detect_unmapped_genes(
    pavprot_df: pd.DataFrame,
    ref_faa: Optional[str] = None,
    qry_faa: Optional[str] = None,
    ref_gff: Optional[str] = None,
    query_gff: Optional[str] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect Scenarios G and H: Genes without mappings.

    Scenario G: Reference genes not in pavprot output
    Scenario H: Query genes not in pavprot output

    Args:
        pavprot_df: DataFrame from pavprot output
        ref_faa: Path to reference protein FASTA
        qry_faa: Path to query protein FASTA
        ref_gff: Path to reference GFF3 (alternative to ref_faa)
        query_gff: Path to query GFF3 (alternative to qry_faa)

    Returns:
        Tuple of (unmapped_ref_df, unmapped_query_df)
    """
    # Get mapped genes from pavprot output
    mapped_old_genes = set(pavprot_df['old_gene'].unique())
    mapped_new_genes = set(pavprot_df['new_gene'].unique())

    print(f"  Mapped ref genes in pavprot: {len(mapped_old_genes)}")
    print(f"  Mapped query genes in pavprot: {len(mapped_new_genes)}")

    # Get all reference genes
    all_old_genes = set()
    if ref_gff and os.path.exists(ref_gff):
        print(f"  Getting ref genes from GFF: {ref_gff}")
        all_old_genes = parse_gff_gene_ids(ref_gff)
    elif ref_faa and os.path.exists(ref_faa):
        print(f"  Getting ref genes from FASTA: {ref_faa}")
        all_old_genes = parse_fasta_ids(ref_faa, is_query=False)

    # Get all query genes
    all_new_genes = set()
    if query_gff and os.path.exists(query_gff):
        print(f"  Getting query genes from GFF: {query_gff}")
        all_new_genes = parse_gff_gene_ids(query_gff)
    elif qry_faa and os.path.exists(qry_faa):
        print(f"  Getting query genes from FASTA: {qry_faa}")
        all_new_genes = parse_fasta_ids(qry_faa, is_query=True)

    print(f"  Total ref genes found: {len(all_old_genes)}")
    print(f"  Total query genes found: {len(all_new_genes)}")

    # Calculate unmapped genes
    unmapped_ref = all_old_genes - mapped_old_genes
    unmapped_query = all_new_genes - mapped_new_genes

    print(f"  Unmapped ref genes (Scenario G): {len(unmapped_ref)}")
    print(f"  Unmapped query genes (Scenario H): {len(unmapped_query)}")

    # Get transcript info from GFF files
    ref_gff_tx = {}
    query_gff_tx = {}
    if ref_gff and os.path.exists(ref_gff):
        print(f"  Parsing transcripts from ref GFF...")
        ref_gff_tx = parse_gff_transcripts(ref_gff)
    if query_gff and os.path.exists(query_gff):
        print(f"  Parsing transcripts from query GFF...")
        query_gff_tx = parse_gff_transcripts(query_gff)

    # Create DataFrames with transcript info
    unmapped_ref_records = []
    for gene_id in sorted(unmapped_ref):
        tx_list, tx_count = ref_gff_tx.get(gene_id, ([], 0))
        unmapped_ref_records.append({
            'gene_id': gene_id,
            'transcripts': ';'.join(tx_list) if tx_list else '',
            'transcript_count': tx_count,
            'scenario': 'G',
            'description': 'old_gene_no_query_match'
        })
    unmapped_ref_df = pd.DataFrame(unmapped_ref_records)

    unmapped_query_records = []
    for gene_id in sorted(unmapped_query):
        tx_list, tx_count = query_gff_tx.get(gene_id, ([], 0))
        unmapped_query_records.append({
            'gene_id': gene_id,
            'transcripts': ';'.join(tx_list) if tx_list else '',
            'transcript_count': tx_count,
            'scenario': 'H',
            'description': 'new_gene_no_ref_match'
        })
    unmapped_query_df = pd.DataFrame(unmapped_query_records)

    return unmapped_ref_df, unmapped_query_df


# =============================================================================
# Main Function
# =============================================================================

def create_argument_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Detect advanced gene mapping scenarios (E, A, B, J, C/D/I, F, G, H)"
    )

    parser.add_argument(
        '--pavprot-output',
        required=True,
        help='Path to pavprot TSV output file'
    )
    parser.add_argument(
        '--ref-faa',
        help='Path to reference protein FASTA'
    )
    parser.add_argument(
        '--qry-faa',
        help='Path to query protein FASTA'
    )
    parser.add_argument(
        '--gff',
        help='Comma-separated GFF3 files: ref.gff,query.gff'
    )
    parser.add_argument(
        '--scenarios',
        default='E,A,B,J,CDI,G,H',
        help='Comma-separated scenarios to detect (default: E,A,B,J,CDI,G,H). Note: F is DISABLED.'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory (default: auto-named based on scenarios)'
    )
    parser.add_argument(
        '--max-swap-distance',
        type=int,
        default=100000,
        help='Maximum distance for swap detection (default: 100000)'
    )

    return parser


def main():
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Parse scenarios
    scenarios = [s.strip().upper() for s in args.scenarios.split(',')]
    print(f"\n{'='*80}")
    print(f"DETECTING ADVANCED SCENARIOS: {', '.join(scenarios)}")
    print(f"{'='*80}\n")

    # Validate inputs
    if not os.path.exists(args.pavprot_output):
        print(f"Error: Pavprot output not found: {args.pavprot_output}", file=sys.stderr)
        sys.exit(1)

    # Parse GFF files
    ref_gff, query_gff = None, None
    if args.gff:
        gff_files = [f.strip() for f in args.gff.split(',')]
        if len(gff_files) >= 1:
            ref_gff = gff_files[0]
        if len(gff_files) >= 2:
            query_gff = gff_files[1]

    # Create output directory
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # Auto-name based on scenarios
        scenario_str = '_'.join(sorted(scenarios))
        input_basename = Path(args.pavprot_output).stem
        output_dir = f"scenarios_{scenario_str}_output"

    output_dir = Path(args.pavprot_output).parent / output_dir
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}\n")

    # Load pavprot output
    print(f"Loading pavprot output: {args.pavprot_output}")
    pavprot_df = pd.read_csv(args.pavprot_output, sep='\t')
    print(f"  Loaded {len(pavprot_df)} entries\n")

    results_summary = []

    # =========================================================================
    # IMPORTANT: Detect CDI FIRST to get exclusion sets for A, B, J
    # CDI takes priority - genes in CDI are NOT counted in A, B, or J
    # =========================================================================
    cdi_old_genes, cdi_new_genes = get_cdi_genes(pavprot_df)
    print(f"CDI exclusion sets: {len(cdi_old_genes)} ref genes, {len(cdi_new_genes)} query genes\n")

    # Detect E (1:1 orthologs) - exclusive by definition
    if 'E' in scenarios:
        print("=" * 60)
        print("Detecting Scenario E (1:1 Orthologs)")
        print("=" * 60)
        ortho_df = detect_one_to_one_orthologs(pavprot_df)
        if len(ortho_df) > 0:
            output_file = output_dir / 'scenario_E_1to1_orthologs.tsv'
            ortho_df.to_csv(output_file, sep='\t', index=False)
            print(f"  Output: {output_file}\n")
            results_summary.append(('E', len(ortho_df), str(output_file)))
        else:
            print("  No 1:1 orthologs found\n")
            results_summary.append(('E', 0, 'N/A'))

    # Detect A (1:2N mappings) - EXCLUSIVE: exactly 2 queries, NOT in CDI
    if 'A' in scenarios:
        print("=" * 60)
        print("Detecting Scenario A (1:2N Mappings - exactly 2 queries, NOT in CDI)")
        print("=" * 60)
        one_to_many_df = detect_one_to_many(pavprot_df, exclude_refs=cdi_old_genes)
        if len(one_to_many_df) > 0:
            output_file = output_dir / 'scenario_A_1to2N_mappings.tsv'
            one_to_many_df.to_csv(output_file, sep='\t', index=False)
            print(f"  Output: {output_file}\n")
            results_summary.append(('A', len(one_to_many_df), str(output_file)))
        else:
            print("  No 1:2N mappings found\n")
            results_summary.append(('A', 0, 'N/A'))

    # Detect B (N:1 mappings) - EXCLUSIVE: NOT in CDI
    if 'B' in scenarios:
        print("=" * 60)
        print("Detecting Scenario B (N:1 Mappings - NOT in CDI)")
        print("=" * 60)
        many_to_one_df = detect_many_to_one(pavprot_df, exclude_queries=cdi_new_genes)
        if len(many_to_one_df) > 0:
            output_file = output_dir / 'scenario_B_Nto1_mappings.tsv'
            many_to_one_df.to_csv(output_file, sep='\t', index=False)
            print(f"  Output: {output_file}\n")
            results_summary.append(('B', len(many_to_one_df), str(output_file)))
        else:
            print("  No N:1 mappings found\n")
            results_summary.append(('B', 0, 'N/A'))

    # Detect J (1:2N+ mappings, 3+ queries) - EXCLUSIVE: NOT in CDI
    if 'J' in scenarios:
        print("=" * 60)
        print("Detecting Scenario J (1:2N+ Mappings - 3+ queries, NOT in CDI)")
        print("=" * 60)
        complex_df = detect_complex_one_to_many(pavprot_df, min_count=3, exclude_refs=cdi_old_genes)
        if len(complex_df) > 0:
            output_file = output_dir / 'scenario_J_1to2N_plus_mappings.tsv'
            complex_df.to_csv(output_file, sep='\t', index=False)
            print(f"  Output: {output_file}\n")
            results_summary.append(('J', len(complex_df), str(output_file)))
        else:
            print("  No 1:2N+ mappings found\n")
            results_summary.append(('J', 0, 'N/A'))

    # Detect CDI (cross-mapping groups)
    if 'CDI' in scenarios:
        print("=" * 60)
        print("Detecting Scenario CDI (Cross-Mapping Classification)")
        print("=" * 60)
        cross_df = classify_cross_mappings(pavprot_df)
        if len(cross_df) > 0:
            output_file = output_dir / 'scenario_CDI_cross_mappings.tsv'
            cross_df.to_csv(output_file, sep='\t', index=False)
            print(f"  Output: {output_file}\n")
            results_summary.append(('CDI', len(cross_df), str(output_file)))
        else:
            print("  No cross-mappings to classify\n")
            results_summary.append(('CDI', 0, 'N/A'))

    # Detect F [DISABLED]
    if 'F' in scenarios:
        print("=" * 60)
        print("Scenario F (Positional Swaps) - DISABLED")
        print("=" * 60)
        print("  ⚠️  Scenario F is DISABLED (2026-01-09)")
        print("  Reason: 100% overlap with E scenario detected.")
        print("  See docs/SCENARIO_IMPLEMENTATION.md for details.\n")
        results_summary.append(('F', -1, 'DISABLED - 100% E overlap'))

    # Detect G, H
    if 'G' in scenarios or 'H' in scenarios:
        print("=" * 60)
        print("Detecting Scenarios G, H (Unmapped Genes)")
        print("=" * 60)

        unmapped_ref_df, unmapped_query_df = detect_unmapped_genes(
            pavprot_df,
            ref_faa=args.ref_faa,
            qry_faa=args.qry_faa,
            ref_gff=ref_gff,
            query_gff=query_gff
        )

        if 'G' in scenarios and len(unmapped_ref_df) > 0:
            output_file = output_dir / 'scenario_G_unmapped_old_genes.tsv'
            unmapped_ref_df.to_csv(output_file, sep='\t', index=False)
            print(f"  Output Scenario G: {output_file}")
            results_summary.append(('G', len(unmapped_ref_df), str(output_file)))
        elif 'G' in scenarios:
            results_summary.append(('G', 0, 'N/A'))

        if 'H' in scenarios and len(unmapped_query_df) > 0:
            output_file = output_dir / 'scenario_H_unmapped_new_genes.tsv'
            unmapped_query_df.to_csv(output_file, sep='\t', index=False)
            print(f"  Output Scenario H: {output_file}")
            results_summary.append(('H', len(unmapped_query_df), str(output_file)))
        elif 'H' in scenarios:
            results_summary.append(('H', 0, 'N/A'))

        print()

    # Print summary
    print("=" * 80)
    print("DETECTION COMPLETE")
    print("=" * 80)
    print(f"\nOutput directory: {output_dir}\n")
    print("Results summary:")
    print("-" * 60)
    for scenario, count, filepath in results_summary:
        status = "entries" if count >= 0 else ""
        print(f"  Scenario {scenario}: {count} {status}")
        if filepath != 'N/A' and count > 0:
            print(f"    → {filepath}")
    print("-" * 60)

    # Save summary
    summary_file = output_dir / 'detection_summary.txt'
    with open(summary_file, 'w') as f:
        f.write(f"Advanced Scenario Detection Summary\n")
        f.write(f"{'='*60}\n\n")
        f.write(f"Input: {args.pavprot_output}\n")
        f.write(f"Scenarios detected: {', '.join(scenarios)}\n\n")
        f.write(f"Results:\n")
        for scenario, count, filepath in results_summary:
            f.write(f"  Scenario {scenario}: {count}\n")
            if filepath != 'N/A' and count > 0:
                f.write(f"    File: {filepath}\n")

    print(f"\nSummary saved to: {summary_file}")


if __name__ == '__main__':
    main()
