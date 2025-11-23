"""Unit tests for PAVprot class"""
import pytest
import os
import tempfile
from pathlib import Path
from pavprot import PAVprot


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


class TestFasta2Dict:
    """Tests for PAVprot.fasta2dict method"""

    @pytest.mark.unit
    def test_basic_fasta_parsing(self, sample_fasta):
        """Test parsing a standard FASTA file"""
        result = list(PAVprot.fasta2dict(sample_fasta, is_query=False))

        assert len(result) == 3
        assert result[0][0] == "XP_001234"
        assert result[0][1] == "MATKLLVVGASDFLKJWE"
        assert result[1][0] == "XP_005678"
        assert result[1][1] == "MGKWVTFISLLFLFSSAYS"
        assert result[2][0] == "XP_009999"
        assert result[2][1] == "MAHHHHHHKKKK"

    @pytest.mark.unit
    def test_multiline_sequence_concatenation(self, sample_fasta):
        """Test that multi-line sequences are properly concatenated"""
        result = list(PAVprot.fasta2dict(sample_fasta, is_query=False))

        # First sequence is split across two lines in the file
        assert result[0][1] == "MATKLLVVGASDFLKJWE"
        assert '\n' not in result[0][1]

    @pytest.mark.unit
    def test_header_parsing_with_pipe(self, sample_fasta):
        """Test that headers with pipes are parsed correctly"""
        result = list(PAVprot.fasta2dict(sample_fasta, is_query=False))

        # Should extract only the first part before the pipe
        assert result[0][0] == "XP_001234"
        assert result[1][0] == "XP_005678"

    @pytest.mark.unit
    def test_query_suffix_removal(self, sample_query_fasta):
        """Test that -p suffix is removed from query sequences"""
        result = list(PAVprot.fasta2dict(sample_query_fasta, is_query=True))

        assert len(result) == 3
        # Should remove -p1 suffix
        assert result[0][0] == "MSTRG.100"
        # Should remove -p2 suffix
        assert result[1][0] == "MSTRG.200"
        # No suffix to remove
        assert result[2][0] == "MSTRG.300"

    @pytest.mark.unit
    def test_query_suffix_no_removal_when_not_query(self, sample_query_fasta):
        """Test that -p suffix is NOT removed when is_query=False"""
        result = list(PAVprot.fasta2dict(sample_query_fasta, is_query=False))

        # Should keep the suffix
        assert result[0][0] == "MSTRG.100-p1"
        assert result[1][0] == "MSTRG.200-p2"

    @pytest.mark.unit
    def test_uppercase_conversion(self):
        """Test that sequences are converted to uppercase"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
            f.write(">seq1\n")
            f.write("atcg\n")
            f.write("tgca\n")
            temp_file = f.name

        try:
            result = list(PAVprot.fasta2dict(temp_file, is_query=False))
            assert result[0][1] == "ATCGTGCA"
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_empty_lines_ignored(self):
        """Test that empty lines are properly ignored"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
            f.write(">seq1\n")
            f.write("ATCG\n")
            f.write("\n")  # Empty line
            f.write("TGCA\n")
            f.write("\n")  # Another empty line
            f.write(">seq2\n")
            f.write("GGGG\n")
            temp_file = f.name

        try:
            result = list(PAVprot.fasta2dict(temp_file, is_query=False))
            assert len(result) == 2
            assert result[0][1] == "ATCGTGCA"
            assert result[1][1] == "GGGG"
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_empty_file(self):
        """Test parsing an empty FASTA file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
            temp_file = f.name

        try:
            result = list(PAVprot.fasta2dict(temp_file, is_query=False))
            assert result == []
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_only_headers_no_sequences(self):
        """Test file with only headers and no sequences"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
            f.write(">seq1\n")
            f.write(">seq2\n")
            temp_file = f.name

        try:
            result = list(PAVprot.fasta2dict(temp_file, is_query=False))
            # Both sequences should be yielded with empty sequences
            assert len(result) == 2
            assert result[0][0] == "seq1"
            assert result[0][1] == ""
            assert result[1][0] == "seq2"
            assert result[1][1] == ""
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_header_with_spaces(self):
        """Test that headers with spaces are parsed correctly"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
            f.write(">seq1 some description here\n")
            f.write("ATCG\n")
            temp_file = f.name

        try:
            result = list(PAVprot.fasta2dict(temp_file, is_query=False))
            # Should only extract the first word
            assert result[0][0] == "seq1"
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_query_suffix_edge_cases(self):
        """Test edge cases for -p suffix removal"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.fasta') as f:
            f.write(">AB-p1 has suffix\n")
            f.write("ATCG\n")
            f.write(">ABC-p2 has suffix\n")
            f.write("GGGG\n")
            f.write(">A-p3 too short\n")
            f.write("CCCC\n")
            f.write(">ABCD-x9 wrong suffix\n")
            f.write("TTTT\n")
            temp_file = f.name

        try:
            result = list(PAVprot.fasta2dict(temp_file, is_query=True))
            # AB-p1: len=5 >= 3, pos -3 is '-', pos -2 is 'p', should remove
            assert result[0][0] == "AB"
            # ABC-p2: len=6 >= 3, should remove
            assert result[1][0] == "ABC"
            # A-p3: len=4 >= 3, pos -3 (idx 1) is '-', pos -2 (idx 2) is 'p', should remove
            assert result[2][0] == "A"
            # ABCD-x9: doesn't match pattern (pos -2 is not 'p'), should NOT remove
            assert result[3][0] == "ABCD-x9"
        finally:
            os.unlink(temp_file)


class TestLoadGFF:
    """Tests for PAVprot.load_gff method"""

    @pytest.mark.unit
    def test_basic_gff_parsing(self, sample_gff):
        """Test parsing a standard GFF3 file"""
        rna_to_protein, locus_to_gene = PAVprot.load_gff(sample_gff)

        # Check RNA to protein mapping
        assert "XM_001234" in rna_to_protein
        assert rna_to_protein["XM_001234"] == "XP_001234.1"
        assert "XM_005678" in rna_to_protein
        assert rna_to_protein["XM_005678"] == "XP_005678.2"

    @pytest.mark.unit
    def test_genbank_vs_protein_id(self, sample_gff):
        """Test that both GenBank and protein_id attributes are handled"""
        rna_to_protein, locus_to_gene = PAVprot.load_gff(sample_gff)

        # First entry has both GenBank and protein_id
        assert rna_to_protein["XM_001234"] == "XP_001234.1"
        # Second entry has only protein_id
        assert rna_to_protein["XM_005678"] == "XP_005678.2"

    @pytest.mark.unit
    def test_missing_protein_id(self, sample_gff):
        """Test handling of CDS without protein_id or GenBank"""
        rna_to_protein, locus_to_gene = PAVprot.load_gff(sample_gff)

        # XM_009999 has neither GenBank nor protein_id, should not be in mapping
        assert "XM_009999" not in rna_to_protein

    @pytest.mark.unit
    def test_locus_to_gene_mapping(self, sample_gff):
        """Test locus_tag to gene ID mapping"""
        rna_to_protein, locus_to_gene = PAVprot.load_gff(sample_gff)

        assert "LOC100" in locus_to_gene
        assert locus_to_gene["LOC100"] == "gene-LOC100"
        assert "LOC200" in locus_to_gene
        assert locus_to_gene["LOC200"] == "gene-LOC200"

    @pytest.mark.unit
    def test_non_cds_lines_ignored(self, sample_gff):
        """Test that non-CDS lines are ignored"""
        rna_to_protein, locus_to_gene = PAVprot.load_gff(sample_gff)

        # The file has gene, mRNA, and exon lines, but we only process CDS
        # So we should only have 3 locus tags (from CDS lines)
        assert len(locus_to_gene) == 3

    @pytest.mark.unit
    def test_comment_lines_ignored(self):
        """Test that comment lines are properly ignored"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as f:
            f.write("##gff-version 3\n")
            f.write("# This is a comment\n")
            f.write("NC_000001.11\tRefSeq\tCDS\t100\t200\t.\t+\t0\t")
            f.write("ID=cds-XP_001;Parent=rna-XM_001;protein_id=XP_001.1\n")
            temp_file = f.name

        try:
            rna_to_protein, locus_to_gene = PAVprot.load_gff(temp_file)
            assert "XM_001" in rna_to_protein
            assert rna_to_protein["XM_001"] == "XP_001.1"
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_malformed_attributes(self):
        """Test handling of malformed attribute strings"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as f:
            f.write("NC_000001.11\tRefSeq\tCDS\t100\t200\t.\t+\t0\t")
            f.write("ID=cds-XP_001;Parent=rna-XM_001;malformed_no_equals;protein_id=XP_001.1\n")
            temp_file = f.name

        try:
            rna_to_protein, locus_to_gene = PAVprot.load_gff(temp_file)
            # Should still parse correctly despite malformed attribute
            assert "XM_001" in rna_to_protein
            assert rna_to_protein["XM_001"] == "XP_001.1"
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_parent_without_rna_prefix(self):
        """Test that Parent without 'rna-' prefix is ignored"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as f:
            f.write("NC_000001.11\tRefSeq\tCDS\t100\t200\t.\t+\t0\t")
            f.write("ID=cds-XP_001;Parent=gene-LOC100;protein_id=XP_001.1\n")
            temp_file = f.name

        try:
            rna_to_protein, locus_to_gene = PAVprot.load_gff(temp_file)
            # Parent doesn't start with 'rna-', so no RNA mapping
            assert len(rna_to_protein) == 0
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_empty_gff_file(self):
        """Test parsing an empty GFF file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gff3') as f:
            temp_file = f.name

        try:
            rna_to_protein, locus_to_gene = PAVprot.load_gff(temp_file)
            assert rna_to_protein == {}
            assert locus_to_gene == {}
        finally:
            os.unlink(temp_file)


class TestParseTracking:
    """Tests for PAVprot.parse_tracking method"""

    @pytest.mark.unit
    def test_basic_tracking_parsing(self, sample_tracking):
        """Test parsing a standard tracking file"""
        full, filtered = PAVprot.parse_tracking(sample_tracking)

        assert len(full) >= 3
        assert "LOC100" in full
        assert "LOC200" in full
        assert "LOC300" in full

    @pytest.mark.unit
    def test_class_code_em_conversion(self, sample_tracking):
        """Test that '=' class code is converted to 'em'"""
        full, filtered = PAVprot.parse_tracking(sample_tracking)

        # First entry has '=' which should be converted to 'em'
        loc100_entries = full["LOC100"]
        assert len(loc100_entries) > 0
        assert loc100_entries[0]["class_code"] == "em"

    @pytest.mark.unit
    def test_class_code_filtering(self, sample_tracking):
        """Test that class code filtering works correctly"""
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            filter_codes={"em"}
        )

        # filtered should only contain 'em' class codes
        for entries in filtered.values():
            for entry in entries:
                assert entry["class_code"] == "em"

    @pytest.mark.unit
    def test_multiple_class_code_filtering(self, sample_tracking):
        """Test filtering with multiple class codes"""
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            filter_codes={"em", "j"}
        )

        # Should contain both 'em' and 'j' entries
        all_codes = set()
        for entries in filtered.values():
            for entry in entries:
                all_codes.add(entry["class_code"])

        assert "em" in all_codes
        assert "j" in all_codes
        assert "c" not in all_codes  # 'c' should be filtered out

    @pytest.mark.unit
    def test_with_feature_table(self, sample_tracking, sample_gff):
        """Test parsing with feature table for ID mapping"""
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            feature_table=sample_gff
        )

        # Check that RNA IDs were mapped to protein IDs
        loc100_entries = full["gene-LOC100"]
        assert len(loc100_entries) > 0
        # Should be mapped to protein ID from GFF
        assert loc100_entries[0]["ref_transcript"] == "XP_001234.1"

    @pytest.mark.unit
    def test_ref_field_validation(self):
        """Test that invalid reference fields are skipped"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tracking') as f:
            f.write("TCONS_1\tXLOC_1\t-\t=\tq1:MSTRG.100|MSTRG.100.1|5\n")
            f.write("TCONS_2\tXLOC_2\tLOC100\t=\tq1:MSTRG.200|MSTRG.200.1|3\n")  # No pipe
            f.write("TCONS_3\tXLOC_3\tLOC200|XM_001\t=\tq1:MSTRG.300|MSTRG.300.1|4\n")  # Valid
            temp_file = f.name

        try:
            full, filtered = PAVprot.parse_tracking(temp_file)
            # Only the third entry should be parsed
            assert len(full) == 1
            assert "LOC200" in full
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_query_info_parsing(self, sample_tracking):
        """Test that query info is parsed correctly"""
        full, filtered = PAVprot.parse_tracking(sample_tracking)

        loc100_entries = full["LOC100"]
        entry = loc100_entries[0]

        assert entry["query_gene"] == "MSTRG.100"
        assert entry["query_transcript"] == "MSTRG.100.1"
        assert entry["exons"] == 5

    @pytest.mark.unit
    def test_exon_parsing_with_invalid_value(self):
        """Test handling of invalid exon counts"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tracking') as f:
            f.write("TCONS_1\tXLOC_1\tLOC100|XM_001\t=\tq1:MSTRG.100|MSTRG.100.1|invalid\n")
            temp_file = f.name

        try:
            full, filtered = PAVprot.parse_tracking(temp_file)
            entry = full["LOC100"][0]
            # Should be None when ValueError is caught
            assert entry["exons"] is None
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_insufficient_query_fields(self):
        """Test that entries with insufficient query fields are skipped"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tracking') as f:
            f.write("TCONS_1\tXLOC_1\tLOC100|XM_001\t=\tq1:MSTRG.100|2\n")  # Only 2 parts
            f.write("TCONS_2\tXLOC_2\tLOC200|XM_002\t=\tq1:MSTRG.200|MSTRG.200.1|3\n")  # Valid
            temp_file = f.name

        try:
            full, filtered = PAVprot.parse_tracking(temp_file)
            # Only second entry should be parsed
            assert len(full) == 1
            assert "LOC200" in full
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_rna_prefix_removal(self, sample_tracking, sample_gff):
        """Test that 'rna-' prefix is removed for mapping"""
        full, filtered = PAVprot.parse_tracking(
            sample_tracking,
            feature_table=sample_gff
        )

        # The tracking file has 'rna-XM_001234', GFF maps 'XM_001234' to protein
        loc100_entries = full["gene-LOC100"]
        assert loc100_entries[0]["ref_transcript"] == "XP_001234.1"

    @pytest.mark.unit
    def test_empty_tracking_file(self):
        """Test parsing an empty tracking file"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tracking') as f:
            temp_file = f.name

        try:
            full, filtered = PAVprot.parse_tracking(temp_file)
            assert full == {}
            assert filtered == {}
        finally:
            os.unlink(temp_file)

    @pytest.mark.unit
    def test_comment_lines_ignored(self):
        """Test that comment lines are properly ignored"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tracking') as f:
            f.write("# This is a comment\n")
            f.write("TCONS_1\tXLOC_1\tLOC100|XM_001\t=\tq1:MSTRG.100|MSTRG.100.1|5\n")
            temp_file = f.name

        try:
            full, filtered = PAVprot.parse_tracking(temp_file)
            assert len(full) == 1
            assert "LOC100" in full
        finally:
            os.unlink(temp_file)
