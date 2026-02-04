#!/usr/bin/env python3
"""
Tests for mapping_multiplicity.py module.

Tests the detect_multiple_mappings function for identifying
one-to-many and many-to-one gene mappings.
"""

import unittest
import os
import sys
import tempfile
import shutil
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from mapping_multiplicity import detect_multiple_mappings


class TestMappingMultiplicity(unittest.TestCase):
    """Tests for detect_multiple_mappings function."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_tsv(self, data, filename="test_mapping.tsv"):
        """Helper to create a test TSV file."""
        filepath = os.path.join(self.test_dir, filename)
        df = pd.DataFrame(data)
        df.to_csv(filepath, sep='\t', index=False)
        return filepath

    def test_one_to_many_detection(self):
        """Test detection of one ref gene mapping to multiple query genes."""
        # Create test data: old_gene1 maps to new_gene1 and new_gene2
        data = {
            'old_gene': ['old_gene1', 'old_gene1', 'old_gene2'],
            'old_transcript': ['ref_t1', 'ref_t1', 'ref_t2'],
            'new_gene': ['new_gene1', 'new_gene2', 'new_gene3'],
            'new_transcript': ['query_t1', 'query_t2', 'query_t3'],
            'transcript_pair_class_code': ['=', 'j', '=']
        }
        filepath = self._create_test_tsv(data)
        output_prefix = os.path.join(self.test_dir, "test_output")

        detect_multiple_mappings(filepath, output_prefix)

        # Check that one-to-many output file was created
        ref_multi_file = f"{output_prefix}_old_to_multiple_new.tsv"
        self.assertTrue(os.path.exists(ref_multi_file))

        # Read and verify content
        df = pd.read_csv(ref_multi_file, sep='\t')
        self.assertEqual(len(df), 1)  # Only old_gene1 has multiple queries
        self.assertEqual(df.iloc[0]['old_gene'], 'old_gene1')
        self.assertEqual(df.iloc[0]['num_new_genes'], 2)

    def test_many_to_one_detection(self):
        """Test detection of multiple ref genes mapping to one query gene."""
        # Create test data: old_gene1 and old_gene2 both map to new_gene1
        data = {
            'old_gene': ['old_gene1', 'old_gene2', 'old_gene3'],
            'old_transcript': ['ref_t1', 'ref_t2', 'ref_t3'],
            'new_gene': ['new_gene1', 'new_gene1', 'new_gene2'],
            'new_transcript': ['query_t1', 'query_t1', 'query_t2'],
            'transcript_pair_class_code': ['=', 'j', '=']
        }
        filepath = self._create_test_tsv(data)
        output_prefix = os.path.join(self.test_dir, "test_output")

        detect_multiple_mappings(filepath, output_prefix)

        # Check that many-to-one output file was created
        qry_multi_file = f"{output_prefix}_new_to_multiple_old.tsv"
        self.assertTrue(os.path.exists(qry_multi_file))

        # Read and verify content
        df = pd.read_csv(qry_multi_file, sep='\t')
        self.assertEqual(len(df), 1)  # Only new_gene1 has multiple refs
        self.assertEqual(df.iloc[0]['new_gene'], 'new_gene1')
        self.assertEqual(df.iloc[0]['num_old_genes'], 2)

    def test_no_multiple_mappings(self):
        """Test with data that has no multiple mappings."""
        # Create test data with 1:1 mappings only
        data = {
            'old_gene': ['old_gene1', 'old_gene2', 'old_gene3'],
            'old_transcript': ['ref_t1', 'ref_t2', 'ref_t3'],
            'new_gene': ['new_gene1', 'new_gene2', 'new_gene3'],
            'new_transcript': ['query_t1', 'query_t2', 'query_t3'],
            'transcript_pair_class_code': ['=', '=', '=']
        }
        filepath = self._create_test_tsv(data)
        output_prefix = os.path.join(self.test_dir, "test_output")

        detect_multiple_mappings(filepath, output_prefix)

        # Check that output files were created but are empty (header only)
        ref_multi_file = f"{output_prefix}_old_to_multiple_new.tsv"
        qry_multi_file = f"{output_prefix}_new_to_multiple_old.tsv"

        self.assertTrue(os.path.exists(ref_multi_file))
        self.assertTrue(os.path.exists(qry_multi_file))

        # Verify no data rows (only header)
        df_ref = pd.read_csv(ref_multi_file, sep='\t')
        df_qry = pd.read_csv(qry_multi_file, sep='\t')
        self.assertEqual(len(df_ref), 0)
        self.assertEqual(len(df_qry), 0)

    def test_default_output_prefix(self):
        """Test that default output prefix is derived from input filename."""
        data = {
            'old_gene': ['old_gene1'],
            'old_transcript': ['ref_t1'],
            'new_gene': ['new_gene1'],
            'new_transcript': ['query_t1'],
            'transcript_pair_class_code': ['=']
        }
        filepath = self._create_test_tsv(data, "my_mapping_file.tsv")

        # Call without output_prefix
        detect_multiple_mappings(filepath)

        # Check that output files use input filename as prefix
        expected_prefix = os.path.join(self.test_dir, "my_mapping_file")
        ref_multi_file = f"{expected_prefix}_old_to_multiple_new.tsv"
        self.assertTrue(os.path.exists(ref_multi_file))


if __name__ == '__main__':
    unittest.main()
