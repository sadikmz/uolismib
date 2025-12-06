#!/usr/bin/env python3
"""
Real Data Workflow: Gene Structure Change Analysis
===================================================
This script demonstrates how to run the analysis with your actual genome data.

Requirements:
    - BioPython: pip install biopython --break-system-packages
    - pandas: pip install pandas --break-system-packages
    - BLAST+: installed on system

Input files needed:
    1. reference.gff3 - Reference genome annotation
    2. updated.gff3 - Updated genome annotation
    3. reference_proteins.fasta - Reference protein sequences
    4. updated_proteins.fasta - Updated protein sequences
"""

import subprocess
import sys
import os
from pathlib import Path
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from .analyzer import (
    GFFParser, BlastAnalyzer, GeneStructureAnalyzer,
    ResultsExporter, Gene, BlastHit
)
from .clustering import DiamondClusterer
import tempfile


class DetectGeneSplitMerge:
    """Detect gene splits and merges between genome assemblies."""

    def __init__(self, ref_gff, ref_proteins, upd_gff, upd_proteins, output_dir,
                 threads=28, run_clustering=False, clustering_workflow='linclust',
                 clustering_params=None):
        """
        Initialize workflow with file paths.

        Args:
            ref_gff: Path to reference GFF file
            ref_proteins: Path to reference protein FASTA
            upd_gff: Path to updated GFF file
            upd_proteins: Path to updated protein FASTA
            output_dir: Directory for output files
            threads: Number of CPU threads for alignment
            run_clustering: Whether to run DIAMOND clustering (default: False)
            clustering_workflow: Clustering workflow (linclust, cluster, deepclust, etc.)
            clustering_params: Additional clustering parameters (space-separated string)
        """
        self.ref_gff = Path(ref_gff)
        self.ref_proteins = Path(ref_proteins)
        self.upd_gff = Path(upd_gff)
        self.upd_proteins = Path(upd_proteins)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.threads = threads
        self.run_clustering = run_clustering
        self.clustering_workflow = clustering_workflow
        self.clustering_params = clustering_params

        # DIAMOND alignment output files
        self.forward_blast = self.output_dir / "forward_diamond.tsv"
        self.reverse_blast = self.output_dir / "reverse_diamond.tsv"

        # DIAMOND databases
        self.ref_db = self.output_dir / "ref_db"
        self.upd_db = self.output_dir / "upd_db"

        # Clustering outputs
        self.clustering_outputs = {}

    def create_databases(self):
        """
        Create DIAMOND databases from protein sequences.
        """
        print("\n" + "="*60)
        print("Creating DIAMOND Databases")
        print("="*60)

        # Create reference database
        print(f"\nCreating reference database...")
        cmd_ref = [
            'diamond', 'makedb',
            '--in', str(self.ref_proteins),
            '--db', str(self.ref_db)
        ]

        try:
            result = subprocess.run(cmd_ref, check=True, capture_output=True, text=True)
            print(f"✓ Reference database created: {self.ref_db}.dmnd")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error creating reference database: {e.stderr}")
            return False
        except FileNotFoundError:
            print("✗ Error: diamond not found. Is DIAMOND installed?")
            return False

        # Create updated database
        print(f"\nCreating updated database...")
        cmd_upd = [
            'diamond', 'makedb',
            '--in', str(self.upd_proteins),
            '--db', str(self.upd_db)
        ]

        try:
            result = subprocess.run(cmd_upd, check=True, capture_output=True, text=True)
            print(f"✓ Updated database created: {self.upd_db}.dmnd")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error creating updated database: {e.stderr}")
            return False

        return True

    def diamond_blastp(self):
        """
        Run DIAMOND BLASTP in both directions (reciprocal alignment).
        """
        print("\n" + "="*60)
        print("Running Reciprocal DIAMOND BLASTP")
        print("="*60)
        # Forward DIAMOND: ref -> updated
        print(f"\nRunning forward DIAMOND BLASTP (ref -> updated)...")
        print(f"⏳ This is much faster than NCBI BLAST...")

        cmd_forward = [
            'diamond', 'blastp',
            '--query', str(self.ref_proteins),
            '--db', str(self.upd_db),
            '--out', str(self.forward_blast),
            '--outfmt', '6', 'qseqid', 'sseqid', 'pident', 'length', 'mismatch',
                        'gapopen', 'qstart', 'qend', 'sstart', 'send', 'evalue',
                        'bitscore', 'qlen', 'slen',
            '--evalue', '1e-10',
            '--max-target-seqs', '10',
            '--threads', str(self.threads),
            '--ultra-sensitive'
        ]

        try:
            result = subprocess.run(cmd_forward, check=True, capture_output=True, text=True)
            print(f"✓ Forward DIAMOND BLASTP completed: {self.forward_blast}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error in forward DIAMOND BLASTP: {e.stderr}")
            return False
        except FileNotFoundError:
            print("✗ Error: diamond not found. Is DIAMOND installed?")
            return False

        # Reverse DIAMOND: updated -> ref
        print(f"\nRunning reverse DIAMOND BLASTP (updated -> ref)...")

        cmd_reverse = [
            'diamond', 'blastp',
            '--query', str(self.upd_proteins),
            '--db', str(self.ref_db),
            '--out', str(self.reverse_blast),
            '--outfmt', '6', 'qseqid', 'sseqid', 'pident', 'length', 'mismatch',
                        'gapopen', 'qstart', 'qend', 'sstart', 'send', 'evalue',
                        'bitscore', 'qlen', 'slen',
            '--evalue', '1e-10',
            '--max-target-seqs', '10',
            '--threads', str(self.threads),
            '--ultra-sensitive'
        ]

        try:
            result = subprocess.run(cmd_reverse, check=True, capture_output=True, text=True)
            print(f"✓ Reverse DIAMOND BLASTP completed: {self.reverse_blast}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error in reverse DIAMOND BLASTP: {e.stderr}")
            return False

        return True
    
    def parse_data(self):
        """
        Parse GFF files and BLAST results.
        """
        print("\n" + "="*60)
        print("Parsing Input Data")
        print("="*60)
        
        # Parse GFF files
        print("\nParsing GFF files...")
        ref_genes = GFFParser.parse_gff(str(self.ref_gff))
        upd_genes = GFFParser.parse_gff(str(self.upd_gff))
        
        # Add protein sequences
        print("\nAdding protein sequences...")
        GFFParser.add_protein_sequences(ref_genes, str(self.ref_proteins))
        GFFParser.add_protein_sequences(upd_genes, str(self.upd_proteins))
        
        # Get protein lengths for BLAST parsing
        ref_lens = {gid: len(g.protein_seq) for gid, g in ref_genes.items()}
        upd_lens = {gid: len(g.protein_seq) for gid, g in upd_genes.items()}
        
        # Parse BLAST results
        print("\nParsing BLAST results...")
        forward_hits = BlastAnalyzer.parse_blast_outfmt6(
            str(self.forward_blast), ref_lens, upd_lens
        )
        reverse_hits = BlastAnalyzer.parse_blast_outfmt6(
            str(self.reverse_blast), upd_lens, ref_lens
        )
        
        # Filter BLAST hits
        print("\nFiltering BLAST hits...")
        forward_filtered = BlastAnalyzer.filter_hits(
            forward_hits,
            min_identity=80.0,
            min_coverage=70.0,
            max_evalue=1e-10
        )
        reverse_filtered = BlastAnalyzer.filter_hits(
            reverse_hits,
            min_identity=80.0,
            min_coverage=70.0,
            max_evalue=1e-10
        )
        
        return ref_genes, upd_genes, forward_filtered, reverse_filtered
    
    def analyze(self, ref_genes, upd_genes, forward_hits, reverse_hits):
        """
        Run the gene structure analysis.
        """
        print("\n" + "="*60)
        print("Analyzing Gene Structure Changes")
        print("="*60)
        
        # Initialize analyzer
        analyzer = GeneStructureAnalyzer(
            ref_genes=ref_genes,
            upd_genes=upd_genes,
            forward_blast=forward_hits,
            reverse_blast=reverse_hits
        )
        
        # Detect changes
        splits = analyzer.detect_splits(min_confidence=0.7)
        merges = analyzer.detect_merges(min_confidence=0.7)
        
        return splits, merges
    
    def export_results(self, splits, merges):
        """
        Export and summarize results.
        """
        print("\n" + "="*60)
        print("Exporting Results")
        print("="*60)
        
        # Save to files
        if splits:
            splits_file = self.output_dir / "gene_splits.tsv"
            ResultsExporter.save_results(splits, str(splits_file))
            print(f"\n✓ Gene splits saved to: {splits_file}")
        
        if merges:
            merges_file = self.output_dir / "gene_merges.tsv"
            ResultsExporter.save_results(merges, str(merges_file))
            print(f"✓ Gene merges saved to: {merges_file}")
        
        # Print summary
        ResultsExporter.print_summary(splits, merges)

        return splits, merges

    def diamond_clustering(self):
        """
        Run DIAMOND clustering on reference, query, and combined protein sets.
        Runs iteratively for ref, qry, and combined (all) modes.
        """
        if not self.run_clustering:
            return

        print("\n" + "="*60)
        print("DIAMOND Clustering (Optional)")
        print("="*60)

        # Parse additional parameters
        extra_params = self._parse_clustering_params()

        # Initialize clusterer
        try:
            clusterer = DiamondClusterer()
        except Exception as e:
            print(f"⚠ Warning: Could not initialize DIAMOND clusterer: {e}")
            print("  Skipping clustering step")
            return

        # Run clustering for each mode
        modes = ['ref', 'qry', 'all']

        for mode in modes:
            print(f"\n--- Clustering mode: {mode} ---")

            try:
                # Prepare input file and output name
                if mode == 'ref':
                    input_file = self.ref_proteins
                    base_name = input_file.stem  # e.g., "reference_proteins"
                    output_file = self.output_dir / f"{base_name}_diamond_{self.clustering_workflow}_clusters.tsv"

                elif mode == 'qry':
                    input_file = self.upd_proteins
                    base_name = input_file.stem  # e.g., "updated_proteins"
                    output_file = self.output_dir / f"{base_name}_diamond_{self.clustering_workflow}_clusters.tsv"

                elif mode == 'all':
                    # Create combined file with renamed IDs
                    input_file = self._create_combined_proteins()
                    base_name = "combined"
                    output_file = self.output_dir / f"{base_name}_diamond_{self.clustering_workflow}_clusters.tsv"

                print(f"  Input:  {input_file}")
                print(f"  Output: {output_file}")

                # Run clustering
                if self.clustering_workflow == 'linclust':
                    df = clusterer.linclust(
                        input_file=str(input_file),
                        output_file=str(output_file),
                        threads=self.threads,
                        **extra_params
                    )
                elif self.clustering_workflow == 'cluster':
                    df = clusterer.cluster(
                        input_file=str(input_file),
                        output_file=str(output_file),
                        threads=self.threads,
                        **extra_params
                    )
                elif self.clustering_workflow == 'deepclust':
                    df = clusterer.deepclust(
                        input_file=str(input_file),
                        output_file=str(output_file),
                        threads=self.threads,
                        **extra_params
                    )
                else:
                    print(f"  ⚠ Unknown clustering workflow: {self.clustering_workflow}")
                    continue

                # Store output
                self.clustering_outputs[mode] = {
                    'output_file': output_file,
                    'dataframe': df
                }

                # Print brief summary
                if df is not None:
                    print(f"  ✓ Clustered {len(df)} sequences into {df['cluster_number'].nunique()} clusters")
                    cluster_sizes = df.groupby('cluster_number').size()
                    print(f"    Singletons: {(cluster_sizes == 1).sum()}")
                    print(f"    Multi-member clusters: {(cluster_sizes > 1).sum()}")

            except Exception as e:
                print(f"  ✗ Error clustering {mode}: {e}")
                continue

        print(f"\n✓ Clustering completed for all modes")

    def _parse_clustering_params(self):
        """Parse clustering parameters from space-separated string."""
        if not self.clustering_params:
            return {}

        params = {}
        tokens = self.clustering_params.split()
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.startswith('--'):
                key = token.lstrip('-').replace('-', '_')

                if i + 1 < len(tokens) and not tokens[i + 1].startswith('--'):
                    value = tokens[i + 1]
                    params[key] = value
                    i += 2
                else:
                    params[key] = True
                    i += 1
            else:
                i += 1

        return params

    def _create_combined_proteins(self):
        """Create a combined protein file with renamed IDs (_REF and _QRY suffixes)."""
        # Create temporary combined file
        temp_fd, temp_path = tempfile.mkstemp(suffix='_combined.fasta', prefix='cluster_', dir=self.output_dir)
        os.close(temp_fd)

        combined_records = []

        # Read reference proteins and add _REF suffix
        for record in SeqIO.parse(self.ref_proteins, 'fasta'):
            new_record = SeqRecord(
                record.seq,
                id=f"{record.id}_REF",
                description=f"{record.description} [REF]"
            )
            combined_records.append(new_record)

        # Read query proteins and add _QRY suffix
        for record in SeqIO.parse(self.upd_proteins, 'fasta'):
            new_record = SeqRecord(
                record.seq,
                id=f"{record.id}_QRY",
                description=f"{record.description} [QRY]"
            )
            combined_records.append(new_record)

        # Write combined file
        SeqIO.write(combined_records, temp_path, 'fasta')

        return temp_path

    def run_complete_workflow(self):
        """
        Execute the complete workflow.
        """
        print("\n" + "="*70)
        print(" "*15 + "GENE STRUCTURE CHANGE ANALYSIS")
        print(" "*18 + "Real Data Workflow (DIAMOND)")
        print("="*70)

        # Create databases
        if not self.create_databases():
            print("\n✗ Workflow failed: Database creation")
            return None, None

        # Run DIAMOND BLASTP
        if not self.diamond_blastp():
            print("\n✗ Workflow failed: DIAMOND BLASTP")
            return None, None

        # Parse data
        try:
            ref_genes, upd_genes, forward_hits, reverse_hits = self.parse_data()
        except Exception as e:
            print(f"\n✗ Workflow failed: Data parsing - {e}")
            return None, None

        # Analyze
        try:
            splits, merges = self.analyze(
                ref_genes, upd_genes, forward_hits, reverse_hits
            )
        except Exception as e:
            print(f"\n✗ Workflow failed: Analysis - {e}")
            return None, None

        # Export
        try:
            self.export_results(splits, merges)
        except Exception as e:
            print(f"\n✗ Workflow failed: Export - {e}")
            return None, None

        # DIAMOND Clustering (optional)
        if self.run_clustering:
            try:
                self.diamond_clustering()
            except Exception as e:
                print(f"\n⚠ Warning: Clustering failed - {e}")
                print("  Continuing with main workflow...")

        print("\n" + "="*70)
        print(" "*20 + "WORKFLOW COMPLETED!")
        print("="*70 + "\n")

        return splits, merges


def main():
    """
    Main entry point for real data analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Detect gene splits and merges between genome assemblies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:

  Basic usage (without clustering):
    python detect_gene_split_merge.py \\
        --ref-gff reference.gff3 \\
        --ref-proteins reference_proteins.fasta \\
        --upd-gff updated.gff3 \\
        --upd-proteins updated_proteins.fasta \\
        --output results/

  With clustering enabled:
    python detect_gene_split_merge.py \\
        --ref-gff reference.gff3 \\
        --ref-proteins reference_proteins.fasta \\
        --upd-gff updated.gff3 \\
        --upd-proteins updated_proteins.fasta \\
        --output results/ \\
        --run-clustering \\
        --clustering-workflow linclust \\
        --clustering-params "--memory-limit 64G --approx-id 90"

Required tools:
    - DIAMOND (for alignment and clustering)
    - Python packages: biopython, pandas
        """
    )
    
    parser.add_argument(
        '--ref-gff',
        required=True,
        help='Reference genome GFF3 file'
    )
    parser.add_argument(
        '--ref-proteins',
        required=True,
        help='Reference protein FASTA file'
    )
    parser.add_argument(
        '--upd-gff',
        required=True,
        help='Updated genome GFF3 file'
    )
    parser.add_argument(
        '--upd-proteins',
        required=True,
        help='Updated protein FASTA file'
    )
    parser.add_argument(
        '--output',
        default='./results',
        help='Output directory (default: ./results)'
    )
    parser.add_argument(
        '--threads',
        type=int,
        default=28,
        help='Number of CPU threads for DIAMOND alignment (default: 28)'
    )

    # Clustering arguments
    parser.add_argument(
        '--run-clustering',
        action='store_true',
        help='Run DIAMOND clustering on proteins (default: disabled)'
    )
    parser.add_argument(
        '--clustering-workflow',
        type=str,
        default='linclust',
        choices=['linclust', 'cluster', 'deepclust'],
        help='Clustering workflow to use (default: linclust)'
    )
    parser.add_argument(
        '--clustering-params',
        type=str,
        help='Additional clustering parameters (space-separated). '
             'Example: "--memory-limit 64G --approx-id 90 --member-cover 80"'
    )

    args = parser.parse_args()

    # Validate input files
    for filepath in [args.ref_gff, args.ref_proteins, args.upd_gff, args.upd_proteins]:
        if not Path(filepath).exists():
            print(f"✗ Error: File not found: {filepath}")
            sys.exit(1)

    # Run workflow
    workflow = DetectGeneSplitMerge(
        ref_gff=args.ref_gff,
        ref_proteins=args.ref_proteins,
        upd_gff=args.upd_gff,
        upd_proteins=args.upd_proteins,
        output_dir=args.output,
        threads=args.threads,
        run_clustering=args.run_clustering,
        clustering_workflow=args.clustering_workflow,
        clustering_params=args.clustering_params
    )
    
    splits, merges = workflow.run_complete_workflow()
    
    if splits is None and merges is None:
        sys.exit(1)


if __name__ == '__main__':
    # Check if run with arguments
    if len(sys.argv) > 1:
        main()
    else:
        # Show help
        print(__doc__)
        print("\nRun with --help for usage information")
        print("\nExample:")
        print("  python real_data_workflow.py \\")
        print("    --ref-gff reference.gff3 \\")
        print("    --ref-proteins reference_proteins.fasta \\")
        print("    --upd-gff updated.gff3 \\")
        print("    --upd-proteins updated_proteins.fasta \\")
        print("    --output results/")
