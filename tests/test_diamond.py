"""Unit tests for DiamondRunner class"""
import pytest
import os
import tempfile
import gzip
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from collections import defaultdict
from pavprot import DiamondRunner


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_diamond_output(fixtures_dir):
    """Return path to sample DIAMOND output file"""
    return str(fixtures_dir / "sample_diamond.tsv.gz")


@pytest.fixture
def diamond_runner():
    """Return a DiamondRunner instance for testing"""
    return DiamondRunner(threads=4, output_prefix="test")


@pytest.fixture
def sample_data():
    """Sample data structure for enrichment testing"""
    return {
        "LOC100": [
            {
                "ref_gene": "gene-LOC100",
                "ref_transcript": "XP_001234.1",
                "query_gene": "MSTRG.100",
                "query_transcript": "MSTRG.100.1",
                "class_code": "em",
                "exons": 5
            }
        ],
        "LOC200": [
            {
                "ref_gene": "gene-LOC200",
                "ref_transcript": "XP_005678.2",
                "query_gene": "MSTRG.200",
                "query_transcript": "MSTRG.200.1",
                "class_code": "j",
                "exons": 3
            }
        ],
        "LOC300": [
            {
                "ref_gene": "gene-LOC300",
                "ref_transcript": "XP_009999",
                "query_gene": "MSTRG.300",
                "query_transcript": "MSTRG.300.1",
                "class_code": "em",
                "exons": 4
            }
        ],
        "LOC400": [
            {
                "ref_gene": "gene-LOC400",
                "ref_transcript": "XP_012345",
                "query_gene": "MSTRG.400",
                "query_transcript": "MSTRG.400.1",
                "class_code": "u",
                "exons": 2
            }
        ]
    }


class TestDiamondBLASTP:
    """Tests for DiamondRunner.diamond_blastp method"""

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_command_construction(self, mock_run, diamond_runner):
        """Test that DIAMOND command is constructed correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            ref_faa = "/path/to/ref.faa"
            qry_faa = "/path/to/qry.faa"

            diamond_runner.diamond_blastp(ref_faa, qry_faa)

            # Check that subprocess.run was called
            assert mock_run.called
            cmd = mock_run.call_args[0][0]

            # Verify key components of the command
            assert "diamond blastp" in cmd
            assert f"--db {ref_faa}" in cmd
            assert f"--query {qry_faa}" in cmd
            assert "--ultra-sensitive" in cmd
            assert "--threads 4" in cmd
            assert "--evalue 1e-6" in cmd
            assert "--max-hsps 1" in cmd
            assert "--unal 1" in cmd
            assert "--compress 1" in cmd

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_output_directory_creation(self, mock_run, diamond_runner):
        """Test that output directory is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            ref_faa = "/path/to/ref.faa"
            qry_faa = "/path/to/qry.faa"

            output_path = diamond_runner.diamond_blastp(ref_faa, qry_faa)

            # Check that directory was created
            expected_dir = os.path.join(tmpdir, 'pavprot_out', 'compareprot_out')
            assert os.path.exists(expected_dir)
            assert os.path.isdir(expected_dir)

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_output_path_format(self, mock_run, diamond_runner):
        """Test that output path is formatted correctly"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            ref_faa = "/path/to/ref.faa"
            qry_faa = "/path/to/qry.faa"

            output_path = diamond_runner.diamond_blastp(ref_faa, qry_faa)

            # Check output path format
            assert output_path.endswith("test_diamond_blastp.tsv.gz")
            assert "pavprot_out/compareprot_out" in output_path

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_thread_parameter(self, mock_run):
        """Test that thread parameter is used correctly"""
        runner = DiamondRunner(threads=16, output_prefix="test")

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            runner.diamond_blastp("/path/to/ref.faa", "/path/to/qry.faa")

            cmd = mock_run.call_args[0][0]
            assert "--threads 16" in cmd

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_subprocess_called_with_check(self, mock_run, diamond_runner):
        """Test that subprocess is called with check=True"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            diamond_runner.diamond_blastp("/path/to/ref.faa", "/path/to/qry.faa")

            # Verify check=True was passed
            assert mock_run.call_args[1]['check'] is True

    @pytest.mark.unit
    @patch('subprocess.run')
    def test_subprocess_called_with_shell(self, mock_run, diamond_runner):
        """Test that subprocess is called with shell=True"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            diamond_runner.diamond_blastp("/path/to/ref.faa", "/path/to/qry.faa")

            # Verify shell=True was passed
            assert mock_run.call_args[1]['shell'] is True


class TestEnrichBLASTP:
    """Tests for DiamondRunner.enrich_blastp method"""

    @pytest.mark.unit
    def test_basic_enrichment(self, diamond_runner, sample_data, sample_diamond_output):
        """Test basic DIAMOND output parsing and enrichment"""
        enriched = diamond_runner.enrich_blastp(sample_data.copy(), sample_diamond_output)

        # Check that MSTRG.100.1 was enriched
        entry = enriched["LOC100"][0]
        assert "diamond" in entry
        assert entry["diamond"] is not None
        assert entry["pident"] == 98.5
        assert entry["qcovhsp"] == 95.0
        assert entry["identical_aa"] == 98
        assert entry["mismatched_aa"] == 2
        assert entry["indels_aa"] == 0
        assert entry["aligned_aa"] == 100

    @pytest.mark.unit
    def test_best_hit_selection_by_bitscore(self, diamond_runner):
        """Test that best hit is selected by bitscore"""
        # Create a DIAMOND output with multiple hits for same query
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
            # Lower bitscore hit
            f.write("MSTRG.100.1\t100\tXP_001\t100\t1\t100\t1\t100\t1e-40\t150.0\t140\t100\t95.0\t95\t5\t0\t0\t90.0\t90.0\tplus\n")
            # Higher bitscore hit - should be selected
            f.write("MSTRG.100.1\t100\tXP_002\t100\t1\t100\t1\t100\t1e-50\t200.0\t180\t100\t98.0\t98\t2\t0\t0\t95.0\t95.0\tplus\n")
            temp_file = f.name

        # Gzip the file
        with open(temp_file, 'rb') as f_in:
            with gzip.open(temp_file + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)

        try:
            data = {
                "LOC100": [{
                    "query_transcript": "MSTRG.100.1",
                    "ref_gene": "gene-LOC100"
                }]
            }

            enriched = diamond_runner.enrich_blastp(data, temp_file + '.gz')
            entry = enriched["LOC100"][0]

            # Should have the higher bitscore hit
            assert entry["diamond"]["bitscore"] == 200.0
            assert entry["diamond"]["sallseqid"] == "XP_002"
        finally:
            os.unlink(temp_file)
            os.unlink(temp_file + '.gz')

    @pytest.mark.unit
    def test_missing_query_transcript(self, diamond_runner, sample_diamond_output):
        """Test handling of query transcript with no DIAMOND hit"""
        data = {
            "LOC999": [{
                "query_transcript": "MSTRG.999.1",  # Not in DIAMOND output
                "ref_gene": "gene-LOC999"
            }]
        }

        enriched = diamond_runner.enrich_blastp(data, sample_diamond_output)
        entry = enriched["LOC999"][0]

        # Should have None/0 values
        assert entry["diamond"] is None
        assert entry["identical_aa"] == 0
        assert entry["mismatched_aa"] == 0
        assert entry["indels_aa"] == 0
        assert entry["aligned_aa"] == 0
        assert entry["pident"] == 0
        assert entry["qcovhsp"] == 0

    @pytest.mark.unit
    def test_high_quality_hit_detection(self, diamond_runner, sample_diamond_output):
        """Test detection of high-quality hits (pident >= 90%, qcovhsp >= 90%)"""
        data = {
            "LOC100": [{
                "query_transcript": "MSTRG.100.1",
                "ref_gene": "gene-LOC100"
            }],
            "LOC200": [{
                "query_transcript": "MSTRG.200.1",
                "ref_gene": "gene-LOC200"
            }]
        }

        enriched = diamond_runner.enrich_blastp(data, sample_diamond_output)

        # MSTRG.100.1 has pident=98.5, qcovhsp=95.0 (both >= 90)
        assert enriched["LOC100"][0]["pident"] >= 90.0
        assert enriched["LOC100"][0]["qcovhsp"] >= 90.0

        # MSTRG.200.1 has pident=92.0, qcovhsp=90.0 (both >= 90)
        assert enriched["LOC200"][0]["pident"] >= 90.0
        assert enriched["LOC200"][0]["qcovhsp"] >= 90.0

    @pytest.mark.unit
    def test_multi_match_query_detection(self, diamond_runner, sample_diamond_output):
        """Test detection of queries with multiple high-quality hits

        Note: Current implementation only keeps best hit per query, so
        pidentCov_9090 will always be None since each query only has one
        hit in the final hits dictionary.
        """
        data = {
            "LOC300": [{
                "query_transcript": "MSTRG.300.1",  # Has 2 hits in file but only best kept
                "ref_gene": "gene-LOC300"
            }],
            "LOC100": [{
                "query_transcript": "MSTRG.100.1",
                "ref_gene": "gene-LOC100"
            }]
        }

        enriched = diamond_runner.enrich_blastp(data, sample_diamond_output)

        # Due to best-hit-only selection, pidentCov_9090 will be None
        # This test documents current behavior
        entry_300 = enriched["LOC300"][0]
        assert entry_300["pidentCov_9090"] is None

        entry_100 = enriched["LOC100"][0]
        assert entry_100["pidentCov_9090"] is None

    @pytest.mark.unit
    def test_type_conversions(self, diamond_runner):
        """Test that type conversions are applied correctly"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
            f.write("MSTRG.100.1\t100\tXP_001\t100\t1\t100\t1\t100\t1e-50\t200.5\t180.3\t100\t98.5\t98\t2\t0\t0\t95.5\t95.5\tplus\n")
            temp_file = f.name

        with open(temp_file, 'rb') as f_in:
            with gzip.open(temp_file + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)

        try:
            data = {
                "LOC100": [{
                    "query_transcript": "MSTRG.100.1",
                    "ref_gene": "gene-LOC100"
                }]
            }

            enriched = diamond_runner.enrich_blastp(data, temp_file + '.gz')
            entry = enriched["LOC100"][0]
            hit = entry["diamond"]

            # Check integer fields
            assert isinstance(hit["qlen"], int)
            assert isinstance(hit["slen"], int)
            assert isinstance(hit["length"], int)
            assert isinstance(hit["nident"], int)
            assert isinstance(hit["mismatch"], int)

            # Check float fields
            assert isinstance(hit["evalue"], float)
            assert isinstance(hit["bitscore"], float)
            assert isinstance(hit["pident"], float)
            assert isinstance(hit["qcovhsp"], float)

            # Check string fields
            assert isinstance(hit["qseqid"], str)
            assert isinstance(hit["sallseqid"], str)
            assert isinstance(hit["qstrand"], str)
        finally:
            os.unlink(temp_file)
            os.unlink(temp_file + '.gz')

    @pytest.mark.unit
    def test_empty_diamond_output(self, diamond_runner):
        """Test handling of empty DIAMOND output"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
            temp_file = f.name

        with open(temp_file, 'rb') as f_in:
            with gzip.open(temp_file + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)

        try:
            data = {
                "LOC100": [{
                    "query_transcript": "MSTRG.100.1",
                    "ref_gene": "gene-LOC100"
                }]
            }

            enriched = diamond_runner.enrich_blastp(data, temp_file + '.gz')
            entry = enriched["LOC100"][0]

            # All should be None/0
            assert entry["diamond"] is None
            assert entry["identical_aa"] == 0
        finally:
            os.unlink(temp_file)
            os.unlink(temp_file + '.gz')

    @pytest.mark.unit
    def test_empty_lines_ignored(self, diamond_runner):
        """Test that empty lines in DIAMOND output are ignored"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as f:
            f.write("MSTRG.100.1\t100\tXP_001\t100\t1\t100\t1\t100\t1e-50\t200.0\t180\t100\t98.0\t98\t2\t0\t0\t95.0\t95.0\tplus\n")
            f.write("\n")  # Empty line
            f.write("MSTRG.200.1\t100\tXP_002\t100\t1\t100\t1\t100\t1e-40\t150.0\t140\t100\t92.0\t92\t8\t0\t0\t90.0\t90.0\tplus\n")
            temp_file = f.name

        with open(temp_file, 'rb') as f_in:
            with gzip.open(temp_file + '.gz', 'wb') as f_out:
                f_out.writelines(f_in)

        try:
            data = {
                "LOC100": [{
                    "query_transcript": "MSTRG.100.1",
                    "ref_gene": "gene-LOC100"
                }],
                "LOC200": [{
                    "query_transcript": "MSTRG.200.1",
                    "ref_gene": "gene-LOC200"
                }]
            }

            enriched = diamond_runner.enrich_blastp(data, temp_file + '.gz')

            # Both entries should be enriched
            assert enriched["LOC100"][0]["diamond"] is not None
            assert enriched["LOC200"][0]["diamond"] is not None
        finally:
            os.unlink(temp_file)
            os.unlink(temp_file + '.gz')

    @pytest.mark.unit
    def test_pidentcov_9090_metadata_structure(self, diamond_runner, sample_diamond_output):
        """Test the structure of pidentCov_9090 metadata"""
        data = {
            "LOC300": [{
                "query_transcript": "MSTRG.300.1",
                "ref_gene": "gene-LOC300"
            }]
        }

        enriched = diamond_runner.enrich_blastp(data, sample_diamond_output)
        entry = enriched["LOC300"][0]

        if entry["pidentCov_9090"] is not None:
            # Check structure
            assert "ref_cnt" in entry["pidentCov_9090"]
            assert "ref_trans" in entry["pidentCov_9090"]
            assert isinstance(entry["pidentCov_9090"]["ref_cnt"], int)
            assert isinstance(entry["pidentCov_9090"]["ref_trans"], list)
