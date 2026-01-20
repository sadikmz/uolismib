#!/usr/bin/env python3
"""
Shared utility functions for PAVprot plotting modules.

This module provides common data loading and processing functions
used across multiple plotting scripts.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, List, Dict, Any


def load_data(input_file: Union[str, Path]) -> pd.DataFrame:
    """
    Load PAVprot output TSV file.

    This is the basic data loading function used by most plotting scripts.

    Args:
        input_file: Path to PAVprot output TSV file

    Returns:
        pandas DataFrame with loaded data
    """
    df = pd.read_csv(input_file, sep='\t')
    return df


def load_pavprot_data(input_file: Union[str, Path],
                      filter_columns: Optional[List[str]] = None,
                      dropna_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load PAVprot output TSV file with additional processing.

    This function extends load_data() with optional filtering and NA handling.
    Used by plot_ipr_comparison.py and other scripts that need extra processing.

    Args:
        input_file: Path to PAVprot output TSV file
        filter_columns: List of columns to keep (None = keep all)
        dropna_columns: List of columns to check for NA values and drop rows

    Returns:
        pandas DataFrame with loaded and processed data
    """
    df = pd.read_csv(input_file, sep='\t')

    if filter_columns:
        available_cols = [c for c in filter_columns if c in df.columns]
        df = df[available_cols]

    if dropna_columns:
        for col in dropna_columns:
            if col in df.columns:
                df = df.dropna(subset=[col])

    return df


def filter_by_class_type(df: pd.DataFrame,
                         class_types: Optional[List[str]] = None,
                         exclude_types: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter DataFrame by class_type column.

    Args:
        df: Input DataFrame with 'class_type' column
        class_types: List of class types to include (None = include all)
        exclude_types: List of class types to exclude

    Returns:
        Filtered DataFrame
    """
    if 'class_type' not in df.columns:
        return df

    if class_types:
        df = df[df['class_type'].isin(class_types)]

    if exclude_types:
        df = df[~df['class_type'].isin(exclude_types)]

    return df


def filter_by_scenario(df: pd.DataFrame,
                       scenarios: Optional[List[str]] = None,
                       exclude_scenarios: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Filter DataFrame by scenario column.

    Args:
        df: Input DataFrame with 'scenario' column
        scenarios: List of scenarios to include (None = include all)
        exclude_scenarios: List of scenarios to exclude

    Returns:
        Filtered DataFrame
    """
    if 'scenario' not in df.columns:
        return df

    if scenarios:
        df = df[df['scenario'].isin(scenarios)]

    if exclude_scenarios:
        df = df[~df['scenario'].isin(exclude_scenarios)]

    return df


def add_ipr_status_column(df: pd.DataFrame,
                          ref_col: str = 'ref_total_ipr_length',
                          query_col: str = 'query_total_ipr_length') -> pd.DataFrame:
    """
    Add IPR status column based on presence of IPR domains.

    Args:
        df: Input DataFrame
        ref_col: Column name for reference IPR length
        query_col: Column name for query IPR length

    Returns:
        DataFrame with added 'ipr_status' column
    """
    df = df.copy()

    def get_status(row):
        ref_has = row.get(ref_col, 0) > 0 if pd.notna(row.get(ref_col)) else False
        query_has = row.get(query_col, 0) > 0 if pd.notna(row.get(query_col)) else False

        if ref_has and query_has:
            return 'both'
        elif ref_has:
            return 'ref_only'
        elif query_has:
            return 'query_only'
        else:
            return 'neither'

    if ref_col in df.columns and query_col in df.columns:
        df['ipr_status'] = df.apply(get_status, axis=1)

    return df


def calculate_summary_stats(df: pd.DataFrame,
                            group_by: str,
                            value_col: str) -> pd.DataFrame:
    """
    Calculate summary statistics grouped by a column.

    Args:
        df: Input DataFrame
        group_by: Column to group by
        value_col: Column to calculate statistics for

    Returns:
        DataFrame with summary statistics
    """
    if group_by not in df.columns or value_col not in df.columns:
        return pd.DataFrame()

    stats = df.groupby(group_by)[value_col].agg([
        'count', 'mean', 'std', 'min', 'max', 'median'
    ]).reset_index()

    return stats


def get_column_if_exists(df: pd.DataFrame,
                         primary_col: str,
                         fallback_cols: Optional[List[str]] = None) -> Optional[str]:
    """
    Get column name, checking for alternatives if primary doesn't exist.

    Args:
        df: DataFrame to check
        primary_col: Primary column name to look for
        fallback_cols: List of alternative column names

    Returns:
        Column name that exists, or None if none found
    """
    if primary_col in df.columns:
        return primary_col

    if fallback_cols:
        for col in fallback_cols:
            if col in df.columns:
                return col

    return None


def validate_required_columns(df: pd.DataFrame,
                              required_cols: List[str],
                              raise_error: bool = True) -> bool:
    """
    Validate that required columns exist in DataFrame.

    Args:
        df: DataFrame to validate
        required_cols: List of required column names
        raise_error: Whether to raise ValueError if columns missing

    Returns:
        True if all columns exist, False otherwise

    Raises:
        ValueError: If raise_error=True and columns are missing
    """
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        if raise_error:
            raise ValueError(f"Missing required columns: {missing}")
        return False

    return True
