"""Integration tests for PAVprot pipeline"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from pavprot import PAVprot, DiamondRunner


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_fasta(fixtures_dir):
    """Return path to sample FASTA file"""
    return str(fixtures_dir / "sample.fasta")


@pytest.fixture
def sample_query_fasta(fixtures_dir):
    """Return path to sample query FASTA file"""
    return str(fixtures_dir / "sample_query.fasta")


@pytest.fixture
def sample_gff(fixtures_dir):
    """Return path to sample GFF3 file"""
    return str(fixtures_dir / "sample.gff3")


@pytest.fixture
def sample_tracking(fixtures_dir):
    """Return path to sample tracking file"""
    return str(fixtures_dir / "sample.tracking")


@pytest.fixture
def sample_diamond_output(fixtures_dir):
    """Return path to sample DIAMOND output file"""
    return str(fixtures_dir / "sample_diamond.tsv.gz")


class TestEndToEndPipeline:
    """Integration tests for complete pipeline"""

    @pytest.mark.integration
    def test_basic_pipeline_without_diamond(self, sample_tracking):
        """Test basic pipeline without DIAMOND enrichment"""
        full, filtered = PAVprot.parse_tracking(sample_tracking)

        # Should parse all entries
        assert len(full) >= 3
        assert "LOC100" in full or "gene-LOC100" in full
        assert "LOC200" in full or "gene-LOC200" in full

        # Each entry should have required fields
        for entries in full.values():
            for entry in entries:
                assert "ref_gene" in entry
                assert "ref_transcript" in entry
                assert "query_gene" in entry
                assert "query_transcript" in entry
                assert "class_code" in entry
                assert "exons" in entry

    @pytest.mark.integration
    def test_pipeline_with_gff_mapping(self, sample_tracking, sample_gff):
        """Test pipeline with GFF feature table for ID mapping"""
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            feature_table=sample_gff
        )

        # Check that RNA IDs were mapped to protein IDs
        # Find the LOC100 entry
        loc100_key = None
        for key in full.keys():
            if "LOC100" in key:
                loc100_key = key
                break

        assert loc100_key is not None
        entries = full[loc100_key]
        assert len(entries) > 0

        # Should be mapped to protein ID from GFF
        assert entries[0]["ref_transcript"] == "XP_001234.1"

    @pytest.mark.integration
    def test_pipeline_with_class_filtering(self, sample_tracking):
        """Test pipeline with class code filtering"""
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            filter_codes={"em"}
        )

        # Full should have all entries
        assert len(full) >= 3

        # Filtered should only have 'em' class codes
        for entries in filtered.values():
            for entry in entries:
                assert entry["class_code"] == "em"

    @pytest.mark.integration
    def test_pipeline_with_diamond_enrichment(self, sample_tracking, sample_diamond_output):
        """Test pipeline with DIAMOND output enrichment"""
        full, filtered = PAVprot.parse_tracking(sample_tracking)

        # Enrich with DIAMOND data
        runner = DiamondRunner()
        enriched = runner.enrich_blastp(full, sample_diamond_output)

        # Check that entries were enriched
        found_enriched = False
        for entries in enriched.values():
            for entry in entries:
                if entry.get("diamond") is not None:
                    found_enriched = True
                    # Should have DIAMOND fields
                    assert "pident" in entry
                    assert "qcovhsp" in entry
                    assert "identical_aa" in entry
                    assert "mismatched_aa" in entry
                    assert "indels_aa" in entry
                    assert "aligned_aa" in entry

        assert found_enriched, "No entries were enriched with DIAMOND data"

    @pytest.mark.integration
    def test_complete_pipeline_with_all_features(
        self, sample_tracking, sample_gff, sample_diamond_output
    ):
        """Test complete pipeline with GFF mapping, filtering, and DIAMOND enrichment"""
        # Parse tracking with GFF and filtering
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            feature_table=sample_gff,
            filter_codes={"em", "j"}
        )

        # Enrich with DIAMOND
        runner = DiamondRunner()
        enriched = runner.enrich_blastp(filtered, sample_diamond_output)

        # Verify results
        assert len(enriched) > 0

        # Check that we have properly formatted entries
        for gene_id, entries in enriched.items():
            for entry in entries:
                # Should have base fields
                assert "ref_gene" in entry
                assert "ref_transcript" in entry
                assert "query_gene" in entry
                assert "query_transcript" in entry
                assert "class_code" in entry

                # Class code should be in filter set
                assert entry["class_code"] in {"em", "j"}

                # Should have DIAMOND enrichment fields
                assert "diamond" in entry
                assert "pident" in entry
                assert "qcovhsp" in entry

    @pytest.mark.integration
    def test_fasta_roundtrip(self, sample_fasta, sample_query_fasta):
        """Test reading and writing FASTA files"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.faa') as f:
            output_file = f.name

        try:
            # Read reference FASTA and write to new file
            with open(output_file, 'w') as f:
                for header, seq in PAVprot.fasta2dict(sample_fasta, is_query=False):
                    f.write(f">{header}\n{seq}\n")

            # Read it back
            result = list(PAVprot.fasta2dict(output_file, is_query=False))

            assert len(result) == 3
            assert result[0][0] == "XP_001234"
            assert result[1][0] == "XP_005678"
            assert result[2][0] == "XP_009999"
        finally:
            os.unlink(output_file)

    @pytest.mark.integration
    def test_query_fasta_processing(self, sample_query_fasta):
        """Test processing query FASTA with -p suffix removal"""
        result = list(PAVprot.fasta2dict(sample_query_fasta, is_query=True))

        # Verify all sequences were parsed
        assert len(result) == 3

        # Verify suffix removal
        headers = [h for h, s in result]
        assert "MSTRG.100" in headers
        assert "MSTRG.200" in headers
        assert "MSTRG.300" in headers

        # Verify no -p suffixes remain
        for header, seq in result:
            if len(header) >= 3:
                # If it would have matched the pattern, it should be removed
                if header.endswith("1") or header.endswith("2"):
                    # Check that we don't have -p before the number
                    assert not (len(header) >= 3 and header[-3] == '-' and header[-2] == 'p')

    @pytest.mark.integration
    @patch('subprocess.run')
    def test_diamond_workflow(self, mock_run, sample_fasta, sample_query_fasta):
        """Test DIAMOND workflow (mocked subprocess)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)

            # Prepare FASTA files
            ref_faa_path = os.path.join(tmpdir, "ref.faa")
            qry_faa_path = os.path.join(tmpdir, "qry.faa")

            with open(ref_faa_path, 'w') as f:
                for h, s in PAVprot.fasta2dict(sample_fasta, is_query=False):
                    f.write(f">{h}\n{s}\n")

            with open(qry_faa_path, 'w') as f:
                for h, s in PAVprot.fasta2dict(sample_query_fasta, is_query=True):
                    f.write(f">{h}\n{s}\n")

            # Run DIAMOND (mocked)
            runner = DiamondRunner(threads=4, output_prefix="test")
            output_path = runner.diamond_blastp(ref_faa_path, qry_faa_path)

            # Verify subprocess was called
            assert mock_run.called

            # Verify output path
            assert "test_diamond_blastp.tsv.gz" in output_path

    @pytest.mark.integration
    def test_multi_entry_per_gene(self):
        """Test handling of multiple entries per gene"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tracking') as f:
            f.write("TCONS_1\tXLOC_1\tLOC100|rna-XM_001\tem\tq1:MSTRG.100|MSTRG.100.1|5\n")
            f.write("TCONS_2\tXLOC_1\tLOC100|rna-XM_002\tj\tq1:MSTRG.200|MSTRG.200.1|3\n")
            f.write("TCONS_3\tXLOC_1\tLOC100|rna-XM_003\tem\tq1:MSTRG.300|MSTRG.300.1|4\n")
            temp_file = f.name

        try:
            full, filtered = PAVprot.parse_tracking(temp_file)

            # Should have one gene with multiple entries
            assert "LOC100" in full
            assert len(full["LOC100"]) == 3

            # Verify all entries are present
            transcripts = [e["ref_transcript"] for e in full["LOC100"]]
            assert "XM_001" in transcripts
            assert "XM_002" in transcripts
            assert "XM_003" in transcripts
        finally:
            os.unlink(temp_file)

    @pytest.mark.integration
    def test_edge_case_all_filtered_out(self, sample_tracking):
        """Test when all entries are filtered out"""
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            filter_codes={"nonexistent_code"}
        )

        # Full should have entries
        assert len(full) > 0

        # Filtered should be empty
        assert len(filtered) == 0

    @pytest.mark.integration
    def test_data_consistency_through_pipeline(self, sample_tracking, sample_diamond_output):
        """Test that data remains consistent through the pipeline"""
        # Parse tracking
        full, filtered = PAVprot.parse_tracking(sample_tracking)

        # Get initial count
        initial_genes = set(full.keys())
        initial_entry_count = sum(len(entries) for entries in full.values())

        # Enrich with DIAMOND
        runner = DiamondRunner()
        enriched = runner.enrich_blastp(full, sample_diamond_output)

        # Verify same genes and entry counts
        assert set(enriched.keys()) == initial_genes
        assert sum(len(entries) for entries in enriched.values()) == initial_entry_count

        # Verify all original fields are preserved
        for gene_id in enriched:
            for i, entry in enumerate(enriched[gene_id]):
                original = full[gene_id][i]
                assert entry["ref_gene"] == original["ref_gene"]
                assert entry["ref_transcript"] == original["ref_transcript"]
                assert entry["query_gene"] == original["query_gene"]
                assert entry["query_transcript"] == original["query_transcript"]
                assert entry["class_code"] == original["class_code"]
