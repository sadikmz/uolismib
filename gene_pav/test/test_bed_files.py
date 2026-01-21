#!/usr/bin/env python3
"""
Standalone test script for BED file coverage calculation.
Tests the calculate_bed_coverage_from_file function with actual BED files.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_bed_coverage import calculate_bed_coverage_from_file, calculate_total_coverage


def test_bed_file_1():
    """Test BED file with no overlaps."""
    print("\n" + "="*80)
    print("Test BED File 1: No Overlaps (test_data_1_no_overlap.bed)")
    print("="*80)

    bed_file = "test/test_data_1_no_overlap.bed"

    print("\nBED file contents:")
    with open(bed_file) as f:
        for line in f:
            print(f"  {line.rstrip()}")

    result = calculate_bed_coverage_from_file(bed_file, group_by_column='gene_id')

    print("\nExpected results:")
    print("  gene1: 100 + 51 + 101 = 252 (no overlaps)")
    print("  gene2: 51 + 51 = 102 (no overlaps)")

    print(f"\nActual results:")
    for gene_id, coverage in sorted(result.items()):
        print(f"  {gene_id}: {coverage}")

    # Validate
    assert result['gene1'] == 252, f"gene1: expected 252, got {result['gene1']}"
    assert result['gene2'] == 102, f"gene2: expected 102, got {result['gene2']}"

    print("\n✓ Test BED File 1 PASSED")
    return True


def test_bed_file_2():
    """Test BED file with overlaps."""
    print("\n" + "="*80)
    print("Test BED File 2: With Overlaps (test_data_2_with_overlap.bed)")
    print("="*80)

    bed_file = "test/test_data_2_with_overlap.bed"

    print("\nBED file contents:")
    with open(bed_file) as f:
        for line in f:
            print(f"  {line.rstrip()}")

    result = calculate_bed_coverage_from_file(bed_file, group_by_column='gene_id')

    print("\nExpected results:")
    print("  gene1:")
    print("    Intervals: (1,100), (50,150), (140,200)")
    print("    Merged: (1, 200) = 200")
    print("  gene2:")
    print("    Intervals: (10,50), (40,80), (100,150)")
    print("    Merged: (10, 80), (100, 150) = 71 + 51 = 122")

    print(f"\nActual results:")
    for gene_id, coverage in sorted(result.items()):
        print(f"  {gene_id}: {coverage}")

    # Validate
    assert result['gene1'] == 200, f"gene1: expected 200, got {result['gene1']}"
    assert result['gene2'] == 122, f"gene2: expected 122, got {result['gene2']}"

    print("\n✓ Test BED File 2 PASSED")
    return True


def test_bed_file_3():
    """Test BED file with complex overlaps."""
    print("\n" + "="*80)
    print("Test BED File 3: Complex Overlaps (test_data_3_complex.bed)")
    print("="*80)

    bed_file = "test/test_data_3_complex.bed"

    print("\nBED file contents:")
    with open(bed_file) as f:
        for line in f:
            print(f"  {line.rstrip()}")

    result = calculate_bed_coverage_from_file(bed_file, group_by_column='gene_id')

    print("\nExpected results:")
    print("  geneA:")
    print("    Intervals: (1,50), (30,80), (75,100), (200,300), (250,350)")
    print("    Merged: (1,100), (200,350) = 100 + 151 = 251")
    print("  geneB:")
    print("    Intervals: (100,200), (150,180), (190,250)")
    print("    Merged: (100, 250) = 151")
    print("  geneC:")
    print("    Intervals: (1,1000), (500,600), (800,900)")
    print("    Merged: (1, 1000) = 1000 (all contained in first interval)")

    print(f"\nActual results:")
    for gene_id, coverage in sorted(result.items()):
        print(f"  {gene_id}: {coverage}")

    # Validate
    assert result['geneA'] == 251, f"geneA: expected 251, got {result['geneA']}"
    assert result['geneB'] == 151, f"geneB: expected 151, got {result['geneB']}"
    assert result['geneC'] == 1000, f"geneC: expected 1000, got {result['geneC']}"

    print("\n✓ Test BED File 3 PASSED")
    return True


def test_total_coverage():
    """Test calculating total coverage without grouping."""
    print("\n" + "="*80)
    print("Test: Total Coverage (no grouping)")
    print("="*80)

    bed_file = "test/test_data_1_no_overlap.bed"

    result = calculate_bed_coverage_from_file(bed_file, group_by_column=None)

    print(f"\nBED file: {bed_file}")
    print("Expected: Total of all intervals with overlaps merged")
    print(f"Actual result: {result}")

    assert 'total' in result, "Expected 'total' key in result"
    # Intervals: (1,100), (50,100), (150,200), (200,250), (300,400)
    # After merge (inclusive): (1,100)=100, (150,250)=101, (300,400)=101 = 302
    assert result['total'] == 302, f"Expected 302, got {result['total']}"

    print("✓ Total Coverage Test PASSED")
    return True


def main():
    """Run all BED file tests."""
    print("="*80)
    print("STANDALONE BED FILE COVERAGE TESTING")
    print("="*80)

    try:
        test_bed_file_1()
        test_bed_file_2()
        test_bed_file_3()
        test_total_coverage()

        print("\n" + "="*80)
        print("✓ ALL BED FILE TESTS PASSED!")
        print("="*80)
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
