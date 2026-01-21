#!/usr/bin/env python3
"""
Edge case tests for PAVprot pipeline modules.

Tests handling of:
- Empty input files
- Malformed GFF files
- Missing required columns
- Invalid data formats
"""

import unittest
import os
import sys
import tempfile
import shutil
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from pavprot import PAVprot
from mapping_multiplicity import detect_multiple_mappings


class TestEmptyInputs(unittest.TestCase):
    """Tests for empty input file handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_empty_tracking_file(self):
        """Test handling of empty tracking file."""
        tracking_path = os.path.join(self.test_dir, "empty.tracking")
        with open(tracking_path, 'w') as f:
            f.write("")  # Empty file

        full_dict, filtered_dict = PAVprot.parse_tracking(tracking_path)

        self.assertEqual(len(full_dict), 0)
        self.assertEqual(len(filtered_dict), 0)

    def test_empty_fasta_file(self):
        """Test handling of empty FASTA file."""
        fasta_path = os.path.join(self.test_dir, "empty.faa")
        with open(fasta_path, 'w') as f:
            f.write("")  # Empty file

        result = dict(PAVprot.fasta2dict(fasta_path))
        self.assertEqual(len(result), 0)

    def test_empty_gff_file(self):
        """Test handling of empty GFF file."""
        gff_path = os.path.join(self.test_dir, "empty.gff")
        with open(gff_path, 'w') as f:
            f.write("##gff-version 3\n")  # Only header

        rna_to_protein, locus_to_gene = PAVprot.load_gff(gff_path)

        self.assertEqual(len(rna_to_protein), 0)
        self.assertEqual(len(locus_to_gene), 0)


class TestMalformedInputs(unittest.TestCase):
    """Tests for malformed input handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_gff_with_missing_attributes(self):
        """Test GFF with CDS lines missing required attributes."""
        gff_content = (
            "##gff-version 3\n"
            "chr1\t.\tCDS\t1\t100\t.\t+\t0\tID=cds1\n"  # Missing Parent and protein_id
        )
        gff_path = os.path.join(self.test_dir, "malformed.gff")
        with open(gff_path, 'w') as f:
            f.write(gff_content)

        rna_to_protein, locus_to_gene = PAVprot.load_gff(gff_path)

        # Should return empty dicts without crashing
        self.assertEqual(len(rna_to_protein), 0)
        self.assertEqual(len(locus_to_gene), 0)

    def test_tracking_with_insufficient_columns(self):
        """Test tracking file with insufficient columns."""
        tracking_content = "col1\tcol2\tcol3\n"  # Only 3 columns, need 5
        tracking_path = os.path.join(self.test_dir, "short.tracking")
        with open(tracking_path, 'w') as f:
            f.write(tracking_content)

        full_dict, filtered_dict = PAVprot.parse_tracking(tracking_path)

        # Should return empty dicts without crashing
        self.assertEqual(len(full_dict), 0)

    def test_fasta_with_no_sequences(self):
        """Test FASTA with headers but no sequences."""
        fasta_content = ">seq1\n>seq2\n"  # Headers only
        fasta_path = os.path.join(self.test_dir, "nodata.faa")
        with open(fasta_path, 'w') as f:
            f.write(fasta_content)

        result = dict(PAVprot.fasta2dict(fasta_path))

        # Should handle gracefully (may return empty sequences)
        self.assertIsInstance(result, dict)


class TestMissingColumns(unittest.TestCase):
    """Tests for TSV files with missing required columns."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_mapping_tsv_missing_ref_gene(self):
        """Test mapping TSV missing ref_gene column."""
        # Missing ref_gene column
        data = {
            'ref_transcript': ['t1', 't2'],
            'query_gene': ['q1', 'q2'],
            'query_transcript': ['qt1', 'qt2'],
            'class_code': ['=', '=']
        }
        df = pd.DataFrame(data)
        filepath = os.path.join(self.test_dir, "missing_col.tsv")
        df.to_csv(filepath, sep='\t', index=False)

        # Should raise an error or handle gracefully
        with self.assertRaises((KeyError, ValueError)):
            detect_multiple_mappings(filepath)

    def test_mapping_tsv_missing_query_gene(self):
        """Test mapping TSV missing query_gene column."""
        # Missing query_gene column
        data = {
            'ref_gene': ['r1', 'r2'],
            'ref_transcript': ['t1', 't2'],
            'query_transcript': ['qt1', 'qt2'],
            'class_code': ['=', '=']
        }
        df = pd.DataFrame(data)
        filepath = os.path.join(self.test_dir, "missing_col.tsv")
        df.to_csv(filepath, sep='\t', index=False)

        # Should raise an error or handle gracefully
        with self.assertRaises((KeyError, ValueError)):
            detect_multiple_mappings(filepath)


class TestCommentAndBlankLines(unittest.TestCase):
    """Tests for handling comment lines and blank lines."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_tracking_with_comments(self):
        """Test tracking file with comment lines."""
        tracking_content = (
            "# This is a comment\n"
            "TCONS_00000001\tXLOC_000001\tgene1|rna-T1\t=\tq1:geneA|T1.1|2\n"
            "# Another comment\n"
            "\n"  # Blank line
            "TCONS_00000002\tXLOC_000002\tgene2|rna-T2\t=\tq1:geneB|T2.1|2\n"
        )
        tracking_path = os.path.join(self.test_dir, "comments.tracking")
        with open(tracking_path, 'w') as f:
            f.write(tracking_content)

        full_dict, filtered_dict = PAVprot.parse_tracking(tracking_path)

        # Should parse 2 valid entries, ignoring comments and blanks
        self.assertEqual(len(full_dict), 2)

    def test_gff_with_comments(self):
        """Test GFF with comment lines."""
        gff_content = (
            "##gff-version 3\n"
            "# Comment line\n"
            "##sequence-region chr1 1 1000\n"
            "chr1\t.\tCDS\t1\t100\t.\t+\t0\tID=cds1;Parent=rna-TRNA1;GenBank=PROT1;locus_tag=LOC1\n"
            "# Another comment\n"
        )
        gff_path = os.path.join(self.test_dir, "comments.gff")
        with open(gff_path, 'w') as f:
            f.write(gff_content)

        rna_to_protein, locus_to_gene = PAVprot.load_gff(gff_path)

        self.assertEqual(len(rna_to_protein), 1)
        self.assertEqual(rna_to_protein.get('TRNA1'), 'PROT1')


if __name__ == '__main__':
    unittest.main()
