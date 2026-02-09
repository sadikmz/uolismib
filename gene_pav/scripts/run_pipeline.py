#!/usr/bin/env python3
"""
PAVprot Master Pipeline Script
==============================

This script handles data preparation and integration for the PAVprot analysis workflow.
All plotting has been moved to the plot/ module for better organization.

USAGE:
------
    # Run data integration:
    python run_pipeline.py --task psauron

    # List available tasks:
    python run_pipeline.py --list

PLOTTING:
---------
All plotting functionality has been centralized in the plot/ module.
See plot/__init__.py for available plot generation functions.

    from gene_pav.plot import generate_plots
    generate_plots(output_dir, plot_types=['scenarios', 'quality', 'advanced'])

CONFIGURATION:
--------------
Edit the CONFIG dictionary below to set your input/output paths.

Author: PAVprot Pipeline
Date: 2026-02-09
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import pandas as pd

# =============================================================================
# CONFIGURATION - Edit these paths for your environment
# =============================================================================

CONFIG = {
    # Base directories
    "gene_pav_dir": Path(__file__).parent.parent,  # Updated to point to gene_pav/ directory
    "output_dir": Path(__file__).parent.parent / "plots",  # Output to plots directory

    # Dataset input directory (can be overridden via constructor)
    "dataset_dir": Path(__file__).parent.parent / "pavprot_out_20260209_154955",  # Updated to latest output

    # PAVprot output files (will auto-detect from dataset_dir, preferring enriched versions)
    "transcript_level_tsv": None,  # Will auto-detect from dataset_dir
    "gene_level_tsv": None,        # Will auto-detect from dataset_dir

    # External data files (optional - tasks will skip if not found)
    # These are copied to pavprot output directory by refactored --proteinx-out and --psauron-out parameters
    "psauron_ref": Path(__file__).parent.parent / "pavprot_out_20260209_154955/psauron/ref_all.csv",
    "psauron_qry": Path(__file__).parent.parent / "pavprot_out_20260209_154955/psauron/qry_all.csv",
    "proteinx_ref": Path(__file__).parent.parent / "pavprot_out_20260209_154955/proteinx/GCF_013085055.1_proteinx.tsv",
    "proteinx_qry": Path(__file__).parent.parent / "pavprot_out_20260209_154955/proteinx/Foc47_013085055.1_proteinx.tsv",
    "phytopathogen_list": Path("/Users/sadik/Documents/projects/data/disease_research_supported.csv"),
    "fungidb_gene_stats": Path("/Users/sadik/Documents/projects/data/fungidb_v68_gene_stats.tsv"),

    # Plot settings
    "figure_dpi": 150,
    "figure_format": "png",
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_latest_output(dataset_dir: Path) -> tuple:
    """
    Auto-detect PAVprot output files from a dataset directory.
    Prefers enriched files (*_with_psauron.tsv) if available.

    Args:
        dataset_dir: Path to dataset directory (e.g., pavprotOut/)

    Returns:
        Tuple of (transcript_level_path, gene_level_path)
    """
    transcript_file = None
    gene_file = None

    if dataset_dir.exists():
        # Look for fully enriched gene_level file first
        for f in dataset_dir.glob("gene_level_enriched_all.tsv"):
            gene_file = f
            break

        # Look for enriched gene_level file with psauron scores
        if not gene_file:
            for f in dataset_dir.glob("*gene_level_with_psauron.tsv"):
                gene_file = f
                break

        # Fallback to raw gene_level file if enriched not found
        if not gene_file:
            for f in dataset_dir.glob("*_gene_level.tsv"):
                gene_file = f
                break

        # Look for fully enriched transcript-level file first
        for f in dataset_dir.glob("transcript_level_enriched_all.tsv"):
            transcript_file = f
            break

        # Look for enriched transcript-level file with psauron scores
        if not transcript_file:
            for f in sorted(dataset_dir.glob("*transcript_level_with_psauron.tsv"), reverse=True):
                transcript_file = f
                break

        # Fallback to main gffcomp file without "_gene_level" in name
        if not transcript_file:
            for f in sorted(dataset_dir.glob("*gffcomp*mapping*.tsv"), reverse=True):
                if ("_gene_level" not in f.name and
                    "domain_distribution" not in f.name and
                    "ipr_length" not in f.name and
                    "multiple" not in f.name):
                    transcript_file = f
                    break

    return transcript_file, gene_file


def check_file_exists(filepath: Path, task_name: str) -> bool:
    """Check if file exists and print status."""
    if filepath is None or not filepath.exists():
        print(f"  [SKIP] {task_name}: Input file not found - {filepath}")
        return False
    return True


def mapping_type_to_colon(mapping_type: str) -> str:
    """
    Convert mapping_type from 'to' notation to ':' notation for legend.

    Examples:
        '1to1' -> '1:1'
        '1to2N' -> '1:2N'
        '1to2N+' -> '1:2N+'
        'Nto1' -> 'N:1'
    """
    return mapping_type.replace('to', ':')


# =============================================================================
# PIPELINE RUNNER CLASS
# =============================================================================

class PipelineRunner:
    """
    Master pipeline runner with modular task functions.

    Each task_* method is independent and can be called manually.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gene_pav_dir = Path(config["gene_pav_dir"])
        self.output_dir = Path(config["output_dir"])
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Use specified dataset directory (or default from config)
        self.dataset_dir = Path(config.get("dataset_dir", config["gene_pav_dir"] / "pavprotOut"))

        # Auto-detect PAVprot output if not specified
        if config["transcript_level_tsv"] is None or config["gene_level_tsv"] is None:
            t_file, g_file = find_latest_output(self.dataset_dir)
            self.transcript_tsv = t_file or config["transcript_level_tsv"]
            self.gene_tsv = g_file or config["gene_level_tsv"]
        else:
            self.transcript_tsv = Path(config["transcript_level_tsv"])
            self.gene_tsv = Path(config["gene_level_tsv"])

        # Store loaded data for reuse
        self._transcript_df = None
        self._gene_df = None

        # Track failed plots for reporting
        self.failed_plots = []

    @property
    def transcript_df(self) -> pd.DataFrame:
        """Lazy-load transcript-level data."""
        if self._transcript_df is None and self.transcript_tsv and self.transcript_tsv.exists():
            print(f"  Loading transcript data: {self.transcript_tsv}")
            self._transcript_df = pd.read_csv(self.transcript_tsv, sep='\t')
        return self._transcript_df

    @property
    def gene_df(self) -> pd.DataFrame:
        """Lazy-load gene-level data."""
        if self._gene_df is None and self.gene_tsv and self.gene_tsv.exists():
            print(f"  Loading gene-level data: {self.gene_tsv}")
            self._gene_df = pd.read_csv(self.gene_tsv, sep='\t')
        return self._gene_df

    def task_6_psauron_integration(self) -> Optional[Path]:
        """
        Integrate Psauron scores into PAVprot output files.

        Psauron predicts whether a sequence is a real protein using
        in-frame reading scores. Higher scores indicate better coding potential.

        - Appends psauron scores to transcript-level TSV
        - Calculates mean for gene-level TSV

        Returns:
            Path to integrated gene-level file, or None if skipped
        """
        print("\n[Task 6] Psauron Data Integration")

        ref_file = Path(self.config["psauron_ref"])
        qry_file = Path(self.config["psauron_qry"])

        if not check_file_exists(ref_file, "Psauron ref"):
            return None
        if not check_file_exists(qry_file, "Psauron qry"):
            return None

        if self.transcript_tsv is None or not self.transcript_tsv.exists():
            print("  [SKIP] Transcript-level TSV not found")
            return None

        # Load psauron data (skip first 2 lines which are command info)
        print(f"  Loading Psauron ref: {ref_file}")
        psauron_ref = pd.read_csv(ref_file, skiprows=2)
        print(f"    Loaded {len(psauron_ref)} entries")

        print(f"  Loading Psauron qry: {qry_file}")
        psauron_qry = pd.read_csv(qry_file, skiprows=2)
        print(f"    Loaded {len(psauron_qry)} entries")

        # Rename columns for clarity
        psauron_ref = psauron_ref.rename(columns={
            'description': 'ref_transcript',
            'psauron_is_protein': 'ref_psauron_is_protein',
            'in-frame_score': 'ref_psauron_score'
        })
        psauron_qry = psauron_qry.rename(columns={
            'description': 'query_transcript',
            'psauron_is_protein': 'qry_psauron_is_protein',
            'in-frame_score': 'qry_psauron_score'
        })

        # Load transcript-level data
        print(f"  Loading transcript data: {self.transcript_tsv}")
        transcript_df = pd.read_csv(self.transcript_tsv, sep='\t')
        print(f"    Loaded {len(transcript_df)} transcript pairs")

        # Detect column naming scheme in transcript data
        if 'query_transcript' in transcript_df.columns:
            # NEW NAMING: ref_transcript, query_transcript, ref_gene, query_gene
            ref_trans_col = 'ref_transcript'
            qry_trans_col = 'query_transcript'
            ref_gene_col = 'ref_gene'
            qry_gene_col = 'query_gene'
        else:
            # OLD NAMING: new_transcript, old_transcript, new_gene, old_gene
            ref_trans_col = 'new_transcript'
            qry_trans_col = 'old_transcript'
            ref_gene_col = 'new_gene'
            qry_gene_col = 'old_gene'

        # Merge psauron scores with transcript-level data
        # Left join to keep all original records
        merged_df = transcript_df.merge(
            psauron_ref[['ref_transcript', 'ref_psauron_is_protein', 'ref_psauron_score']].rename(
                columns={'ref_transcript': ref_trans_col}),
            on=ref_trans_col,
            how='left'
        )
        merged_df = merged_df.merge(
            psauron_qry[['query_transcript', 'qry_psauron_is_protein', 'qry_psauron_score']].rename(
                columns={'query_transcript': qry_trans_col}),
            on=qry_trans_col,
            how='left'
        )

        # Save integrated transcript-level file
        transcript_out = self.output_dir / "transcript_level_with_psauron.tsv"
        merged_df.to_csv(transcript_out, sep='\t', index=False)
        print(f"  [DONE] Saved transcript-level: {transcript_out}")

        # Calculate gene-level aggregation (mean of transcript scores)
        gene_agg = merged_df.groupby([qry_gene_col, ref_gene_col]).agg({
            'ref_psauron_score': 'mean',
            'qry_psauron_score': 'mean',
            'ref_psauron_is_protein': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
            'qry_psauron_is_protein': lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else None,
        }).reset_index()

        gene_agg = gene_agg.rename(columns={
            'ref_psauron_score': 'ref_psauron_score_mean',
            'qry_psauron_score': 'qry_psauron_score_mean',
        })

        # Load and merge with existing gene-level data
        if self.gene_tsv and self.gene_tsv.exists():
            gene_df = pd.read_csv(self.gene_tsv, sep='\t')

            # Drop existing psauron columns if present to avoid _x/_y suffixes
            psauron_cols_to_drop = [c for c in gene_df.columns if 'psauron' in c.lower()]
            if psauron_cols_to_drop:
                gene_df = gene_df.drop(columns=psauron_cols_to_drop)

            gene_merged = gene_df.merge(
                gene_agg,
                on=[qry_gene_col, ref_gene_col],
                how='left'
            )

            gene_out = self.output_dir / "gene_level_with_psauron.tsv"
            gene_merged.to_csv(gene_out, sep='\t', index=False)
            print(f"  [DONE] Saved gene-level: {gene_out}")

            # Print summary stats
            ref_matched = merged_df['ref_psauron_score'].notna().sum()
            qry_matched = merged_df['qry_psauron_score'].notna().sum()
            print(f"  Matched ref transcripts: {ref_matched}/{len(merged_df)} ({100*ref_matched/len(merged_df):.1f}%)")
            print(f"  Matched qry transcripts: {qry_matched}/{len(merged_df)} ({100*qry_matched/len(merged_df):.1f}%)")

            return gene_out

        return transcript_out


# =============================================================================
# COMMAND-LINE INTERFACE
# =============================================================================

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="PAVprot Pipeline - Data Preparation & Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --task psauron
      Run Psauron data integration

For plotting, use the plot module:
  from gene_pav.plot import generate_plots
  generate_plots(output_dir, plot_types=['scenarios', 'quality', 'advanced'])
        """
    )

    parser.add_argument('--task', type=str, default='psauron',
                       help='Task to run: psauron (default)')
    parser.add_argument('--dataset', type=str, default=None,
                       help='Path to PAVprot output dataset directory')
    parser.add_argument('--output', type=str, default=None,
                       help='Output directory for results')
    parser.add_argument('--list', action='store_true',
                       help='List available tasks')

    args = parser.parse_args()

    # Show available tasks
    if args.list:
        print("\nAvailable Tasks:")
        print("  - psauron: Integrate Psauron scores into PAVprot output")
        print("\nFor plotting, use the plot module:")
        print("  from gene_pav.plot import generate_plots")
        return

    # Setup configuration
    config = CONFIG.copy()
    if args.dataset:
        config['dataset_dir'] = Path(args.dataset)
    if args.output:
        config['output_dir'] = Path(args.output)

    # Create runner
    runner = PipelineRunner(config)

    # Execute requested task
    if args.task == 'psauron':
        print("\n" + "=" * 60)
        print("PAVprot Pipeline - Data Integration")
        print("=" * 60)
        runner.task_6_psauron_integration()
    else:
        print(f"Unknown task: {args.task}")
        print("Use --list to see available tasks")


if __name__ == "__main__":
    main()

