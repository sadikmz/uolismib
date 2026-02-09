#!/usr/bin/env python3
"""
Data preparation module for PAVprot output enrichment.

This module handles:
- Computing scenario column from mapping counts
- Deriving class_type_gene from gene pair class codes
- Adding mapping_type column from scenarios
- Handling terminology mapping (old/new ↔ ref/query)
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


def compute_scenario(old2new_count: int, new2old_count: int) -> str:
    """
    Compute gene mapping scenario based on count pairs.

    Args:
        old2new_count: Number of new genes mapping to this old gene
        new2old_count: Number of old genes mapping to this new gene

    Returns:
        Scenario code: 'E' (1:1), 'A' (1:N), 'B' (N:1), 'J' (1:3+), 'CDI' (complex)
    """
    if old2new_count == 1 and new2old_count == 1:
        return 'E'  # 1:1 ortholog
    elif old2new_count == 1 and new2old_count == 2:
        return 'A'  # 1:2 split (gene duplication in new)
    elif old2new_count == 2 and new2old_count == 1:
        return 'B'  # 2:1 merge (gene fusion in new)
    elif old2new_count == 1 and new2old_count >= 3:
        return 'J'  # 1:3+ complex duplication
    else:
        return 'CDI'  # Complex/divergent mapping


def extract_class_type_gene(gene_pair_class_code: Optional[str]) -> str:
    """
    Extract primary class type from gene pair class code.

    GFFcompare codes like "em;j;n" are semicolon-separated.
    We extract the first (primary) code and map to simple class type.

    Args:
        gene_pair_class_code: Semicolon-separated GFFcompare codes

    Returns:
        Simplified class type: 'exact', 'split', 'novel', 'merged', or 'unknown'
    """
    if not gene_pair_class_code or not isinstance(gene_pair_class_code, str):
        return 'unknown'

    # Extract first code
    primary_code = gene_pair_class_code.split(';')[0].strip()

    # Map to simple class types
    code_mapping = {
        'em': 'exact',      # exact match
        'e': 'exact',       # exact (single exon)
        'j': 'split',       # intron chain overlap (partial match)
        'c': 'split',       # contained
        'm': 'split',       # contains match
        'n': 'novel',       # novel isoform
        'k': 'novel',       # not in reference
        's': 'split',       # intron chain share
        'o': 'overlap',     # overlap exons
        'x': 'crossmap',    # cross-strand
        'i': 'intronic',    # intronic
        'y': 'intronic',    # intronic
        'p': 'putative',    # putative exon in reference
        'r': 'repeat',      # repeat
        'u': 'unknown',     # unknown
        '=': 'identity',    # identity
    }

    return code_mapping.get(primary_code, 'unknown')


def enrich_pavprot_data(
    df: pd.DataFrame,
    add_scenario: bool = True,
    add_class_type: bool = True,
    add_mapping_type: bool = False,
) -> pd.DataFrame:
    """
    Enrich PAVprot output DataFrame with computed columns.

    Args:
        df: Input DataFrame with PAVprot gene-level output
        add_scenario: Whether to compute scenario column
        add_class_type: Whether to compute class_type_gene column
        add_mapping_type: Whether to add mapping_type column

    Returns:
        Enriched DataFrame with new computed columns
    """
    df = df.copy()

    # Compute scenario column if requested
    if add_scenario and 'scenario' not in df.columns:
        # Look for count columns
        count_cols = {
            'old2new': ['old2newCount', 'old_to_new_count'],
            'new2old': ['new2oldCount', 'new_to_old_count'],
        }

        old2new_col = None
        new2old_col = None

        for primary, alternatives in count_cols.items():
            for col in alternatives:
                if col in df.columns:
                    if primary == 'old2new':
                        old2new_col = col
                    else:
                        new2old_col = col
                    break

        if old2new_col and new2old_col:
            df['scenario'] = df.apply(
                lambda row: compute_scenario(
                    int(row[old2new_col]) if pd.notna(row[old2new_col]) else 0,
                    int(row[new2old_col]) if pd.notna(row[new2old_col]) else 0
                ),
                axis=1
            )
            logger.info("Added scenario column")
        else:
            logger.warning(f"Could not find count columns. Found: {df.columns.tolist()}")

    # Compute class_type_gene column if requested
    if add_class_type and 'class_type_gene' not in df.columns:
        # Look for gene class code column
        class_col = None
        for col in ['gene_pair_class_code', 'class_code_gene', 'transcript_pair_class_code']:
            if col in df.columns:
                class_col = col
                break

        if class_col:
            df['class_type_gene'] = df[class_col].apply(extract_class_type_gene)
            logger.info(f"Added class_type_gene column from {class_col}")

    # Add mapping_type as alias for scenario if requested
    if add_mapping_type and 'mapping_type' not in df.columns:
        if 'scenario' in df.columns:
            df['mapping_type'] = df['scenario']
            logger.info("Added mapping_type column (alias for scenario)")

    return df


def load_and_enrich(
    gene_level_file: Union[str, Path],
    enrich_kwargs: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Load PAVprot output and enrich with computed columns in one step.

    Args:
        gene_level_file: Path to gene-level TSV file
        enrich_kwargs: Keyword arguments to pass to enrich_pavprot_data()

    Returns:
        Enriched DataFrame
    """
    # Load data
    df = pd.read_csv(gene_level_file, sep='\t')
    logger.info(f"Loaded {len(df)} rows from {gene_level_file}")

    # Enrich with default settings if not specified
    if enrich_kwargs is None:
        enrich_kwargs = {
            'add_scenario': True,
            'add_class_type': True,
            'add_mapping_type': False,
        }

    # Enrich data
    df = enrich_pavprot_data(df, **enrich_kwargs)

    return df


def validate_enrichment(df: pd.DataFrame) -> dict:
    """
    Validate that enrichment was successful.

    Args:
        df: Enriched DataFrame

    Returns:
        Dictionary with validation results
    """
    results = {
        'has_scenario': 'scenario' in df.columns,
        'has_class_type': 'class_type_gene' in df.columns,
        'has_mapping_type': 'mapping_type' in df.columns,
    }

    if results['has_scenario']:
        scenario_counts = df['scenario'].value_counts()
        results['scenario_distribution'] = scenario_counts.to_dict()

    if results['has_class_type']:
        class_counts = df['class_type_gene'].value_counts()
        results['class_type_distribution'] = class_counts.to_dict()

    return results


__all__ = [
    'compute_scenario',
    'extract_class_type_gene',
    'enrich_pavprot_data',
    'load_and_enrich',
    'validate_enrichment',
]
