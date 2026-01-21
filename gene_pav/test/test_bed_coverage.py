#!/usr/bin/env python3
"""
Test suite for BED file total coverage calculation with overlap handling.
This module provides a function to calculate the total length coverage from BED files
by properly merging overlapping intervals.
"""

import pandas as pd
from typing import Dict, List, Tuple


def calculate_total_coverage(intervals: List[Tuple[int, int]]) -> int:
    """
    Calculate total coverage length by merging overlapping intervals.

    This function takes a list of intervals (start, end) and returns the total
    length covered after merging overlapping regions. This prevents double-counting
    when domains overlap.

    Algorithm:
    1. Sort intervals by start position
    2. Merge overlapping or adjacent intervals
    3. Sum the lengths of merged intervals

    Args:
        intervals: List of tuples (start, end) where coordinates are inclusive

    Returns:
        Total length covered (sum of merged interval lengths)

    Examples:
        >>> calculate_total_coverage([(1, 10), (15, 20)])
        16  # 10 + 6 = 16 (no overlap)

        >>> calculate_total_coverage([(1, 10), (5, 15)])
        15  # Merged to (1, 15) = 15

        >>> calculate_total_coverage([(1, 10), (5, 15), (20, 25)])
        21  # (1, 15) + (20, 25) = 15 + 6 = 21

        >>> calculate_total_coverage([(1, 5), (2, 3), (4, 10)])
        10  # All merge to (1, 10) = 10
    """
    if not intervals:
        return 0

    # Sort intervals by start position, then by end position
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))

    # Merge overlapping intervals
    merged = []
    current_start, current_end = sorted_intervals[0]

    for start, end in sorted_intervals[1:]:
        # Check if intervals overlap or are adjacent
        # For inclusive coordinates: [1,10] and [11,20] should merge
        if start <= current_end + 1:
            # Overlapping or adjacent - extend current interval
            current_end = max(current_end, end)
        else:
            # No overlap - save current interval and start new one
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    # Don't forget the last interval
    merged.append((current_start, current_end))

    # Calculate total length (inclusive coordinates)
    total_length = sum(end - start + 1 for start, end in merged)

    return total_length


def calculate_bed_coverage_from_file(bed_file: str,
                                     group_by_column: str = None,
                                     start_col: int = 1,
                                     end_col: int = 2,
                                     group_col: int = 0) -> Dict[str, int]:
    """
    Calculate total coverage from a BED file, handling overlapping coordinates.

    Args:
        bed_file: Path to BED format file (tab-separated)
        group_by_column: If provided, group intervals by this column (e.g., gene_id)
                        If None, calculates total coverage across entire file
        start_col: Column index for start coordinate (0-based, default 1)
        end_col: Column index for end coordinate (0-based, default 2)
        group_col: Column index for grouping (0-based, default 0)

    Returns:
        Dictionary mapping group IDs to total coverage length
        If group_by_column is None, returns {'total': coverage_length}

    Examples:
        BED file format (tab-separated):
        gene1    100    200
        gene1    150    250
        gene2    50     100

        >>> calculate_bed_coverage_from_file('test.bed', group_by_column='gene_id')
        {'gene1': 151, 'gene2': 51}
    """
    # Read BED file without header
    try:
        df = pd.read_csv(bed_file, sep='\t', header=None, comment='#')
    except Exception as e:
        raise ValueError(f"Error reading BED file {bed_file}: {e}")

    # Validate columns exist
    max_col = max(start_col, end_col, group_col if group_by_column else 0)
    if len(df.columns) <= max_col:
        raise ValueError(f"BED file has {len(df.columns)} columns, but need at least {max_col + 1}")

    # Calculate coverage
    if group_by_column:
        # Group by the specified column
        coverage_dict = {}
        for group_id, group_df in df.groupby(group_col):
            intervals = list(zip(group_df[start_col], group_df[end_col]))
            coverage = calculate_total_coverage(intervals)
            coverage_dict[str(group_id)] = coverage
        return coverage_dict
    else:
        # Calculate total coverage across entire file
        intervals = list(zip(df[start_col], df[end_col]))
        total_coverage = calculate_total_coverage(intervals)
        return {'total': total_coverage}


def calculate_ipr_coverage_from_dataframe(df: pd.DataFrame,
                                          group_by: str = 'protein_accession') -> Dict[str, int]:
    """
    Calculate total IPR domain coverage from InterProScan DataFrame.
    This is the replacement for total_ipr_length function.

    Args:
        df: DataFrame with columns: protein_accession (or gene_id),
            start_location, stop_location, interpro_accession
        group_by: Column name to group by (default: 'protein_accession')

    Returns:
        Dictionary mapping protein/gene IDs to total IPR coverage length

    Example:
        >>> df = pd.DataFrame({
        ...     'protein_accession': ['P1', 'P1', 'P2'],
        ...     'start_location': [1, 50, 100],
        ...     'stop_location': [100, 150, 200],
        ...     'interpro_accession': ['IPR001', 'IPR002', 'IPR003']
        ... })
        >>> calculate_ipr_coverage_from_dataframe(df)
        {'P1': 150, 'P2': 101}
    """
    if df is None or len(df) == 0:
        return {}

    # Validate required columns
    required_cols = [group_by, 'start_location', 'stop_location']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"DataFrame missing required columns: {missing_cols}")

    coverage_dict = {}

    for group_id, group_df in df.groupby(group_by):
        # Extract intervals
        intervals = list(zip(group_df['start_location'], group_df['stop_location']))
        # Calculate coverage with overlap handling
        coverage = calculate_total_coverage(intervals)
        coverage_dict[group_id] = coverage

    return coverage_dict


def run_tests():
    """Run comprehensive tests for the coverage calculation functions."""

    print("="*80)
    print("Running Comprehensive Tests for BED Coverage Calculation")
    print("="*80)

    # Test 1: No overlaps
    print("\nTest 1: No overlaps")
    intervals = [(1, 10), (15, 20), (25, 30)]
    result = calculate_total_coverage(intervals)
    expected = 10 + 6 + 6  # 22
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 1 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 2: Complete overlap
    print("\nTest 2: Complete overlap (one interval contains another)")
    intervals = [(1, 100), (20, 30)]
    result = calculate_total_coverage(intervals)
    expected = 100
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 2 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 3: Partial overlap
    print("\nTest 3: Partial overlap")
    intervals = [(1, 50), (30, 80)]
    result = calculate_total_coverage(intervals)
    expected = 80  # Merged to (1, 80)
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 3 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 4: Multiple overlaps
    print("\nTest 4: Multiple overlapping intervals")
    intervals = [(1, 20), (10, 30), (25, 40), (50, 60)]
    result = calculate_total_coverage(intervals)
    expected = 40 + 11  # (1, 40) + (50, 60) = 40 + 11 = 51
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 4 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 5: Adjacent intervals (should merge)
    print("\nTest 5: Adjacent intervals")
    intervals = [(1, 10), (11, 20), (21, 30)]
    result = calculate_total_coverage(intervals)
    expected = 30  # All merge to (1, 30)
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 5 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 6: Empty list
    print("\nTest 6: Empty interval list")
    intervals = []
    result = calculate_total_coverage(intervals)
    expected = 0
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 6 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 7: Single interval
    print("\nTest 7: Single interval")
    intervals = [(100, 200)]
    result = calculate_total_coverage(intervals)
    expected = 101
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 7 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 8: Unsorted intervals
    print("\nTest 8: Unsorted intervals")
    intervals = [(50, 60), (1, 10), (30, 40), (5, 35)]
    result = calculate_total_coverage(intervals)
    expected = 40 + 11  # (1, 40) + (50, 60) = 51
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 8 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 9: All intervals overlap into one
    print("\nTest 9: All intervals merge into one")
    intervals = [(1, 10), (5, 15), (12, 20), (18, 25)]
    result = calculate_total_coverage(intervals)
    expected = 25  # All merge to (1, 25)
    print(f"  Intervals: {intervals}")
    print(f"  Expected: {expected}, Got: {result}")
    assert result == expected, f"Test 9 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    # Test 10: DataFrame test
    print("\nTest 10: DataFrame-based calculation")
    df = pd.DataFrame({
        'protein_accession': ['P1', 'P1', 'P1', 'P2', 'P2'],
        'start_location': [1, 50, 30, 100, 200],
        'stop_location': [100, 150, 80, 150, 250],
        'interpro_accession': ['IPR001', 'IPR002', 'IPR003', 'IPR004', 'IPR005']
    })
    result = calculate_ipr_coverage_from_dataframe(df)
    # P1: (1,100), (50,150), (30,80) -> merge to (1, 150) = 150
    # P2: (100,150), (200,250) -> 51 + 51 = 102
    expected = {'P1': 150, 'P2': 102}
    print(f"  Expected: {expected}")
    print(f"  Got: {result}")
    assert result == expected, f"Test 10 failed: expected {expected}, got {result}"
    print("  ✓ PASSED")

    print("\n" + "="*80)
    print("✓ ALL TESTS PASSED!")
    print("="*80)


if __name__ == '__main__':
    run_tests()
