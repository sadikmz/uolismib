#!/usr/bin/env python3
"""
Unified External Tools Module for PAVprot Pipeline

This module provides a unified interface for running external bioinformatics tools
used in the PAVprot pipeline. Each tool is implemented as a method with a common
interface pattern.

Tools supported:
- DIAMOND: BLAST-based protein alignment
- InterProScan: Domain/motif detection
- gffcompare: GFF comparison and tracking
- Liftoff: Annotation liftover
- Psauron: Protein structure quality scoring
- BUSCO: Benchmarking Universal Single-Copy Orthologs
- Pairwise alignment: Protein sequence alignment
"""

import subprocess
import shutil
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Union
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExternalTool(ABC):
    """Abstract base class for external tools"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name"""
        pass

    @property
    @abstractmethod
    def executable(self) -> str:
        """Executable command name"""
        pass

    def check_installed(self) -> bool:
        """Check if the tool is installed and available in PATH"""
        return shutil.which(self.executable) is not None

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """Run the tool with given arguments"""
        pass

    @abstractmethod
    def parse_output(self, output_path: Path) -> Any:
        """Parse the tool's output file"""
        pass


class ToolsRunner:
    """
    Unified external tools module for PAVprot pipeline.

    Provides methods for running and managing external bioinformatics tools.
    Each method follows a common pattern:
    - Check if tool is installed
    - Validate inputs
    - Run tool with appropriate parameters
    - Parse and return results

    Usage:
        runner = ToolsRunner(output_dir="./output")

        # Check tool availability
        runner.check_all_tools()

        # Run DIAMOND
        results = runner.run_diamond(
            query_fasta="query.faa",
            database="ref_db",
            output_prefix="blast_results"
        )
    """

    def __init__(self, output_dir: Union[str, Path] = "./output",
                 temp_dir: Union[str, Path] = "./tmp",
                 dry_run: bool = False):
        """
        Initialize ToolsRunner.

        Args:
            output_dir: Directory for output files
            temp_dir: Directory for temporary files
            dry_run: If True, only print commands without executing
        """
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.dry_run = dry_run

        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Tool executables
        self._tools = {
            "diamond": "diamond",
            "interproscan": "interproscan.sh",
            "gffcompare": "gffcompare",
            "liftoff": "liftoff",
            "psauron": "psauron",
            "busco": "busco",
        }

    def check_tool_installed(self, tool_name: str) -> bool:
        """Check if a specific tool is installed"""
        executable = self._tools.get(tool_name)
        if executable:
            return shutil.which(executable) is not None
        return False

    def check_all_tools(self) -> Dict[str, bool]:
        """Check installation status of all tools"""
        status = {}
        for tool_name in self._tools:
            status[tool_name] = self.check_tool_installed(tool_name)
            logger.info(f"{tool_name}: {'installed' if status[tool_name] else 'NOT FOUND'}")
        return status

    def _run_command(self, cmd: List[str], description: str = "") -> subprocess.CompletedProcess:
        """
        Run a shell command.

        Args:
            cmd: Command as list of strings
            description: Description for logging

        Returns:
            CompletedProcess object
        """
        cmd_str = " ".join(str(c) for c in cmd)
        logger.info(f"Running {description}: {cmd_str}")

        if self.dry_run:
            logger.info("[DRY RUN] Command not executed")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Command failed: {result.stderr}")

        return result

    # =========================================================================
    # DIAMOND
    # =========================================================================

    def run_diamond(self,
                    query_fasta: Union[str, Path],
                    database: Union[str, Path],
                    output_prefix: str,
                    mode: str = "blastp",
                    evalue: float = 1e-5,
                    max_target_seqs: int = 1,
                    threads: int = 4,
                    extra_args: Optional[List[str]] = None) -> Path:
        """
        Run DIAMOND BLAST alignment.

        Args:
            query_fasta: Path to query FASTA file
            database: Path to DIAMOND database (without .dmnd extension)
            output_prefix: Prefix for output files
            mode: DIAMOND mode ('blastp' or 'blastx')
            evalue: E-value threshold
            max_target_seqs: Maximum target sequences per query
            threads: Number of threads
            extra_args: Additional command line arguments

        Returns:
            Path to output file
        """
        output_file = self.output_dir / f"{output_prefix}.diamond.tsv"

        cmd = [
            "diamond", mode,
            "-q", str(query_fasta),
            "-d", str(database),
            "-o", str(output_file),
            "-e", str(evalue),
            "-k", str(max_target_seqs),
            "-p", str(threads),
            "--outfmt", "6", "qseqid", "sseqid", "pident", "length",
            "mismatch", "gapopen", "qstart", "qend", "sstart", "send",
            "evalue", "bitscore"
        ]

        if extra_args:
            cmd.extend(extra_args)

        self._run_command(cmd, "DIAMOND")
        return output_file

    def run_diamond_makedb(self,
                           fasta_file: Union[str, Path],
                           db_name: str) -> Path:
        """Create DIAMOND database from FASTA file"""
        db_path = self.output_dir / db_name

        cmd = [
            "diamond", "makedb",
            "--in", str(fasta_file),
            "-d", str(db_path)
        ]

        self._run_command(cmd, "DIAMOND makedb")
        return db_path

    # =========================================================================
    # InterProScan
    # =========================================================================

    def run_interproscan(self,
                         input_fasta: Union[str, Path],
                         output_prefix: str,
                         applications: Optional[List[str]] = None,
                         formats: Optional[List[str]] = None,
                         cpu: int = 4) -> Path:
        """
        Run InterProScan for domain/motif detection.

        Args:
            input_fasta: Path to input protein FASTA
            output_prefix: Prefix for output files
            applications: List of InterPro applications (e.g., ['Pfam', 'SMART'])
            formats: Output formats (default: ['tsv', 'gff3'])
            cpu: Number of CPUs

        Returns:
            Path to TSV output file
        """
        output_base = self.output_dir / output_prefix

        cmd = [
            "interproscan.sh",
            "-i", str(input_fasta),
            "-o", str(output_base),
            "-cpu", str(cpu),
            "-goterms",
            "-iprlookup"
        ]

        if applications:
            cmd.extend(["-appl", ",".join(applications)])

        if formats:
            cmd.extend(["-f", ",".join(formats)])
        else:
            cmd.extend(["-f", "tsv,gff3"])

        self._run_command(cmd, "InterProScan")
        return Path(f"{output_base}.tsv")

    # =========================================================================
    # gffcompare
    # =========================================================================

    def run_gffcompare(self,
                       query_gff: Union[str, Path],
                       reference_gff: Union[str, Path],
                       output_prefix: str,
                       extra_args: Optional[List[str]] = None) -> Path:
        """
        Run gffcompare to compare GFF annotations.

        Args:
            query_gff: Path to query GFF file
            reference_gff: Path to reference GFF file
            output_prefix: Prefix for output files
            extra_args: Additional arguments

        Returns:
            Path to tracking file
        """
        output_base = self.output_dir / output_prefix

        cmd = [
            "gffcompare",
            "-r", str(reference_gff),
            "-o", str(output_base),
            str(query_gff)
        ]

        if extra_args:
            cmd.extend(extra_args)

        self._run_command(cmd, "gffcompare")
        return Path(f"{output_base}.tracking")

    # =========================================================================
    # Liftoff
    # =========================================================================

    def run_liftoff(self,
                    target_fasta: Union[str, Path],
                    reference_fasta: Union[str, Path],
                    reference_gff: Union[str, Path],
                    output_gff: str,
                    extra_args: Optional[List[str]] = None) -> Path:
        """
        Run Liftoff for annotation liftover.

        Args:
            target_fasta: Path to target genome FASTA
            reference_fasta: Path to reference genome FASTA
            reference_gff: Path to reference GFF annotation
            output_gff: Output GFF filename
            extra_args: Additional arguments

        Returns:
            Path to output GFF file
        """
        output_path = self.output_dir / output_gff

        cmd = [
            "liftoff",
            "-g", str(reference_gff),
            "-o", str(output_path),
            str(target_fasta),
            str(reference_fasta)
        ]

        if extra_args:
            cmd.extend(extra_args)

        self._run_command(cmd, "Liftoff")
        return output_path

    # =========================================================================
    # Psauron
    # =========================================================================

    def run_psauron(self,
                    input_fasta: Union[str, Path],
                    output_prefix: str,
                    extra_args: Optional[List[str]] = None) -> Path:
        """
        Run Psauron for protein structure quality scoring.

        Args:
            input_fasta: Path to input protein FASTA
            output_prefix: Prefix for output files
            extra_args: Additional arguments

        Returns:
            Path to output file
        """
        output_file = self.output_dir / f"{output_prefix}.psauron.tsv"

        cmd = [
            "psauron",
            "-i", str(input_fasta),
            "-o", str(output_file)
        ]

        if extra_args:
            cmd.extend(extra_args)

        self._run_command(cmd, "Psauron")
        return output_file

    # =========================================================================
    # BUSCO
    # =========================================================================

    def run_BUSCO(self,
                  input_file: Union[str, Path],
                  output_dir: str,
                  lineage: str,
                  mode: str = "proteins",
                  cpu: int = 4,
                  extra_args: Optional[List[str]] = None) -> Path:
        """
        Run BUSCO for completeness assessment.

        Args:
            input_file: Path to input file (FASTA or GFF depending on mode)
            output_dir: Output directory name
            lineage: BUSCO lineage dataset (e.g., 'fungi_odb10')
            mode: BUSCO mode ('proteins', 'transcriptome', 'genome')
            cpu: Number of CPUs
            extra_args: Additional arguments

        Returns:
            Path to output directory
        """
        output_path = self.output_dir / output_dir

        cmd = [
            "busco",
            "-i", str(input_file),
            "-o", output_dir,
            "--out_path", str(self.output_dir),
            "-l", lineage,
            "-m", mode,
            "-c", str(cpu)
        ]

        if extra_args:
            cmd.extend(extra_args)

        self._run_command(cmd, "BUSCO")
        return output_path

    # =========================================================================
    # Pairwise Alignment
    # =========================================================================

    def run_pairwise_alignment(self,
                               seq1: str,
                               seq2: str,
                               mode: str = "global",
                               matrix: str = "BLOSUM62",
                               gap_open: float = -10,
                               gap_extend: float = -0.5) -> Dict[str, Any]:
        """
        Run pairwise protein sequence alignment using Biopython.

        Args:
            seq1: First protein sequence
            seq2: Second protein sequence
            mode: Alignment mode ('global' or 'local')
            matrix: Substitution matrix name
            gap_open: Gap opening penalty
            gap_extend: Gap extension penalty

        Returns:
            Dictionary with alignment results
        """
        try:
            from Bio import Align
            from Bio.Align import substitution_matrices
        except ImportError:
            logger.error("Biopython not installed. Install with: pip install biopython")
            return {}

        if self.dry_run:
            logger.info("[DRY RUN] Pairwise alignment not executed")
            return {"dry_run": True}

        aligner = Align.PairwiseAligner()
        aligner.mode = mode
        aligner.substitution_matrix = substitution_matrices.load(matrix)
        aligner.open_gap_score = gap_open
        aligner.extend_gap_score = gap_extend

        alignments = aligner.align(seq1, seq2)

        if alignments:
            best = alignments[0]
            return {
                "score": best.score,
                "alignment": str(best),
                "identity": self._calculate_identity(best),
                "length": best.shape[1]
            }
        return {}

    def _calculate_identity(self, alignment) -> float:
        """Calculate percent identity from alignment"""
        aligned_seq1 = alignment[0]
        aligned_seq2 = alignment[1]
        matches = sum(1 for a, b in zip(aligned_seq1, aligned_seq2) if a == b and a != '-')
        total = alignment.shape[1]
        return (matches / total * 100) if total > 0 else 0.0

    # =========================================================================
    # Annotation Detection
    # =========================================================================

    def detect_annotation_source(self,
                                 gene_id: str,
                                 known_prefixes: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Detect annotation source from gene ID prefix.

        Args:
            gene_id: Gene identifier string
            known_prefixes: Dictionary mapping prefixes to annotation sources
                           e.g., {"GCF_": "NCBI", "FungiDB-": "FungiDB"}

        Returns:
            Dictionary with detected prefix and source
        """
        default_prefixes = {
            "GCF_": "NCBI RefSeq",
            "GCA_": "NCBI GenBank",
            "FungiDB-": "FungiDB",
            "ENSEMBL": "Ensembl",
            "LOC": "NCBI Gene",
        }

        prefixes = known_prefixes or default_prefixes

        for prefix, source in prefixes.items():
            if gene_id.startswith(prefix):
                return {
                    "gene_id": gene_id,
                    "prefix": prefix,
                    "source": source,
                    "is_new": None  # To be determined by comparison
                }

        # Try to extract prefix before common suffixes
        for suffix in ["_gene", "_transcript", "_mRNA", "_CDS"]:
            if suffix in gene_id:
                prefix = gene_id.split(suffix)[0]
                return {
                    "gene_id": gene_id,
                    "prefix": prefix,
                    "source": "Unknown",
                    "is_new": None
                }

        return {
            "gene_id": gene_id,
            "prefix": "Unknown",
            "source": "Unknown",
            "is_new": None
        }


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Command-line interface for ToolsRunner"""
    import argparse

    parser = argparse.ArgumentParser(
        description="PAVprot External Tools Runner"
    )

    parser.add_argument(
        "--check-tools",
        action="store_true",
        help="Check if all external tools are installed"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Output directory (default: ./output)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing"
    )

    args = parser.parse_args()

    runner = ToolsRunner(
        output_dir=args.output_dir,
        dry_run=args.dry_run
    )

    if args.check_tools:
        print("\nChecking external tools installation:")
        print("=" * 40)
        status = runner.check_all_tools()
        print("\nSummary:")
        installed = sum(1 for v in status.values() if v)
        print(f"  Installed: {installed}/{len(status)}")
        if installed < len(status):
            missing = [k for k, v in status.items() if not v]
            print(f"  Missing: {', '.join(missing)}")


if __name__ == "__main__":
    main()
