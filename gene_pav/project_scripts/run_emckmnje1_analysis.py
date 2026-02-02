#!/usr/bin/env python3
"""
Wrapper Script for emckmnje=1 Filtered Analysis
================================================

This script filters PAVprot output for manually reviewed valid gene pairs
(emckmnje=1) and regenerates all figures and statistics.

USAGE:
------
    python run_emckmnje1_analysis.py

OUTPUT DIRECTORIES:
-------------------
    - Tables: gene_pav/output/120126_out/
    - Figures: gene_pav/output/figures_out/120126_out/

WHAT IT DOES:
-------------
    1. Filters gene_level data for emckmnje=1 (15,817 pairs)
    2. Filters transcript_level data for matching genes
    3. Integrates Psauron and ProteinX data
    4. Regenerates all 24 figures (excludes fungidb_analysis)
    5. Computes summary statistics

Author: Wrapper for PAVprot Pipeline
Date: 2026-01-12
"""

import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from run_pipeline import PipelineRunner, CONFIG, find_latest_output


# =============================================================================
# CONFIGURATION FOR FILTERED ANALYSIS
# =============================================================================

OUTPUT_DATE = "120126"  # DDMMYY format as specified

FILTERED_CONFIG = {
    # Base directories
    "gene_pav_dir": SCRIPT_DIR,
    "output_dir": SCRIPT_DIR / "output" / "figures_out" / f"{OUTPUT_DATE}_out",

    # Tables output directory
    "tables_dir": SCRIPT_DIR / "output" / f"{OUTPUT_DATE}_out",

    # External data files (same as original)
    "psauron_ref": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/psauron/ref_all.csv"),
    "psauron_qry": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/psauron/qry_all.csv"),
    "proteinx_ref": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/proteinx/GCF_013085055.1_proteinx.tsv"),
    "proteinx_qry": Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/proteinx/Foc47_013085055.1_proteinx.tsv"),

    # Plot settings
    "figure_dpi": 150,
    "figure_format": "png",

    # Filter column
    "filter_column": "emckmnje",
    "filter_value": 1,
}


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def load_and_filter_data():
    """
    Load original data and filter for emckmnje=1.

    Returns:
        Tuple of (gene_df_filtered, transcript_df_filtered)
    """
    print("=" * 70)
    print("STEP 1: Loading and Filtering Data")
    print("=" * 70)

    # First try to use the pre-integrated file with Psauron data
    integrated_gene_file = SCRIPT_DIR / "figures_out" / "gene_level_with_psauron.tsv"
    integrated_transcript_file = SCRIPT_DIR / "figures_out" / "transcript_level_with_psauron.tsv"

    if integrated_gene_file.exists():
        print(f"\n  Using pre-integrated data with Psauron scores")
        gene_file = integrated_gene_file
        transcript_file = integrated_transcript_file if integrated_transcript_file.exists() else None
    else:
        # Fall back to raw files
        transcript_file, gene_file = find_latest_output(SCRIPT_DIR)

    if not gene_file or not gene_file.exists():
        raise FileNotFoundError(f"Gene-level file not found: {gene_file}")

    print(f"\n  Loading gene-level data: {gene_file}")
    gene_df = pd.read_csv(gene_file, sep='\t')
    print(f"  Total gene pairs: {len(gene_df):,}")

    # Filter for emckmnje=1
    filter_col = FILTERED_CONFIG["filter_column"]
    filter_val = FILTERED_CONFIG["filter_value"]

    if filter_col not in gene_df.columns:
        raise ValueError(f"Filter column '{filter_col}' not found in gene-level data")

    gene_df_filtered = gene_df[gene_df[filter_col] == filter_val].copy()
    print(f"  Filtered gene pairs (emckmnje=1): {len(gene_df_filtered):,}")
    print(f"  Removed pairs: {len(gene_df) - len(gene_df_filtered):,}")

    # Get list of valid genes for transcript filtering
    valid_old_genes = set(gene_df_filtered['old_gene'].dropna())
    valid_new_genes = set(gene_df_filtered['new_gene'].dropna())

    # Load and filter transcript-level data
    transcript_df_filtered = None
    if transcript_file and transcript_file.exists():
        print(f"\n  Loading transcript-level data: {transcript_file}")
        transcript_df = pd.read_csv(transcript_file, sep='\t')
        print(f"  Total transcript pairs: {len(transcript_df):,}")

        # Filter transcripts where both old_gene and new_gene are in valid set
        mask = (
            transcript_df['old_gene'].isin(valid_old_genes) &
            transcript_df['new_gene'].isin(valid_new_genes)
        )
        transcript_df_filtered = transcript_df[mask].copy()
        print(f"  Filtered transcript pairs: {len(transcript_df_filtered):,}")

    return gene_df_filtered, transcript_df_filtered


def integrate_quality_metrics(gene_df, transcript_df):
    """
    Integrate Psauron and ProteinX data into filtered dataframes.

    This replicates the integration done in run_pipeline.py task_6.
    """
    print("\n" + "=" * 70)
    print("STEP 2: Integrating Quality Metrics")
    print("=" * 70)

    # Load Psauron data
    psauron_ref_path = FILTERED_CONFIG["psauron_ref"]
    psauron_qry_path = FILTERED_CONFIG["psauron_qry"]

    if psauron_ref_path.exists() and psauron_qry_path.exists():
        print(f"\n  Loading Psauron reference data: {psauron_ref_path}")
        # Psauron files have 2 header lines before the CSV data
        psauron_ref = pd.read_csv(psauron_ref_path, skiprows=2)
        print(f"  Loading Psauron query data: {psauron_qry_path}")
        psauron_qry = pd.read_csv(psauron_qry_path, skiprows=2)

        # Standardize column names (Psauron output has: description, psauron_is_protein, in-frame_score)
        psauron_ref = psauron_ref.rename(columns={'description': 'protein_id', 'in-frame_score': 'psauron_score'})
        psauron_qry = psauron_qry.rename(columns={'description': 'protein_id', 'in-frame_score': 'psauron_score'})

        # Extract gene ID from protein ID (remove -T1, -PA suffix)
        def extract_gene_id(protein_id):
            if pd.isna(protein_id):
                return None
            protein_id = str(protein_id)
            # Handle various suffixes
            for suffix in ['-T1', '-PA', '-PB', '-PC', '_T1']:
                if suffix in protein_id:
                    return protein_id.split(suffix)[0]
            return protein_id

        psauron_ref['gene_id'] = psauron_ref['protein_id'].apply(extract_gene_id)
        psauron_qry['gene_id'] = psauron_qry['protein_id'].apply(extract_gene_id)

        # Aggregate to gene level (mean score per gene)
        old_gene_scores = psauron_ref.groupby('gene_id')['psauron_score'].mean().reset_index()
        old_gene_scores.columns = ['old_gene', 'ref_psauron']

        qry_gene_scores = psauron_qry.groupby('gene_id')['psauron_score'].mean().reset_index()
        qry_gene_scores.columns = ['new_gene', 'query_psauron']

        # Merge with gene dataframe
        gene_df = gene_df.merge(old_gene_scores, on='old_gene', how='left')
        gene_df = gene_df.merge(qry_gene_scores, on='new_gene', how='left')

        print(f"  Psauron data merged: {gene_df['ref_psauron'].notna().sum():,} ref, {gene_df['query_psauron'].notna().sum():,} query")
    else:
        print("  [SKIP] Psauron data not found")

    # Load ProteinX/pLDDT data
    proteinx_ref_path = FILTERED_CONFIG["proteinx_ref"]
    proteinx_qry_path = FILTERED_CONFIG["proteinx_qry"]

    if proteinx_ref_path.exists() and proteinx_qry_path.exists():
        print(f"\n  Loading ProteinX reference data: {proteinx_ref_path}")
        proteinx_ref = pd.read_csv(proteinx_ref_path, sep='\t')
        print(f"  Loading ProteinX query data: {proteinx_qry_path}")
        proteinx_qry = pd.read_csv(proteinx_qry_path, sep='\t')

        # Get gene IDs from gene_name column (format: XP_031048514.2_sample_0)
        def extract_gene_from_proteinx(name):
            if pd.isna(name):
                return None
            # Remove _sample_X suffix and extract base ID
            name = str(name)
            if '_sample_' in name:
                name = name.split('_sample_')[0]
            return name

        if 'gene_name' in proteinx_ref.columns:
            proteinx_ref['gene_id'] = proteinx_ref['gene_name'].apply(extract_gene_from_proteinx)
        if 'gene_name' in proteinx_qry.columns:
            proteinx_qry['gene_id'] = proteinx_qry['gene_name'].apply(extract_gene_from_proteinx)

        # Find pLDDT column (residue_plddt_mean in ProteinX output)
        plddt_col = None
        for col in ['residue_plddt_mean', 'pLDDT', 'plddt', 'mean_plddt', 'avg_plddt']:
            if col in proteinx_ref.columns:
                plddt_col = col
                break

        if plddt_col:
            # Aggregate to gene level
            ref_plddt = proteinx_ref.groupby('gene_id')[plddt_col].mean().reset_index()
            ref_plddt.columns = ['old_gene', 'ref_plddt']

            qry_plddt = proteinx_qry.groupby('gene_id')[plddt_col].mean().reset_index()
            qry_plddt.columns = ['new_gene', 'query_plddt']

            # Merge
            gene_df = gene_df.merge(ref_plddt, on='old_gene', how='left')
            gene_df = gene_df.merge(qry_plddt, on='new_gene', how='left')

            print(f"  pLDDT data merged: {gene_df['ref_plddt'].notna().sum():,} ref, {gene_df['query_plddt'].notna().sum():,} query")
    else:
        print("  [SKIP] ProteinX data not found")

    return gene_df, transcript_df


def save_filtered_data(gene_df, transcript_df):
    """
    Save filtered dataframes to output directory.
    """
    print("\n" + "=" * 70)
    print("STEP 3: Saving Filtered Data")
    print("=" * 70)

    tables_dir = FILTERED_CONFIG["tables_dir"]
    tables_dir.mkdir(parents=True, exist_ok=True)

    # Save gene-level data
    gene_output = tables_dir / "gene_level_emckmnje1.tsv"
    gene_df.to_csv(gene_output, sep='\t', index=False)
    print(f"\n  Saved: {gene_output}")
    print(f"  Rows: {len(gene_df):,}")

    # Save transcript-level data
    if transcript_df is not None:
        transcript_output = tables_dir / "transcript_level_emckmnje1.tsv"
        transcript_df.to_csv(transcript_output, sep='\t', index=False)
        print(f"\n  Saved: {transcript_output}")
        print(f"  Rows: {len(transcript_df):,}")

    return gene_output, tables_dir / "transcript_level_emckmnje1.tsv" if transcript_df is not None else None


def compute_statistics(gene_df):
    """
    Compute summary statistics for filtered data.
    """
    print("\n" + "=" * 70)
    print("STEP 4: Computing Summary Statistics")
    print("=" * 70)

    stats = []

    # Gene mapping stats
    stats.append(("Gene Mapping", "Total gene pairs (emckmnje=1)", len(gene_df), "Filtered valid pairs"))

    # Scenario distribution
    if 'scenario' in gene_df.columns:
        scenario_counts = gene_df['scenario'].value_counts()
        for scenario, count in scenario_counts.items():
            pct = count / len(gene_df) * 100
            stats.append(("Gene Mapping", f"Scenario {scenario}", count, f"{pct:.1f}%"))

    # Class type distribution
    if 'class_type_gene' in gene_df.columns:
        class_counts = gene_df['class_type_gene'].value_counts()
        for ctype, count in class_counts.items():
            pct = count / len(gene_df) * 100
            stats.append(("Class Type", f"Type {ctype}", count, f"{pct:.1f}%"))

    # Quality metrics - handle both naming conventions
    psauron_ref_col = 'ref_psauron_score_mean' if 'ref_psauron_score_mean' in gene_df.columns else 'ref_psauron'
    psauron_qry_col = 'qry_psauron_score_mean' if 'qry_psauron_score_mean' in gene_df.columns else 'query_psauron'

    if psauron_ref_col in gene_df.columns and psauron_qry_col in gene_df.columns:
        valid = gene_df[[psauron_ref_col, psauron_qry_col]].dropna()
        if len(valid) > 0:
            corr = valid[psauron_ref_col].corr(valid[psauron_qry_col])
            r_squared = corr ** 2
            stats.append(("Quality Metrics", "Psauron Pearson r", f"{corr:.3f}", "Old vs New annotation"))
            stats.append(("Quality Metrics", "Psauron R-squared", f"{r_squared:.3f}", "Correlation strength"))

    plddt_ref_col = 'ref_plddt_mean' if 'ref_plddt_mean' in gene_df.columns else 'ref_plddt'
    plddt_qry_col = 'qry_plddt_mean' if 'qry_plddt_mean' in gene_df.columns else 'query_plddt'

    if plddt_ref_col in gene_df.columns and plddt_qry_col in gene_df.columns:
        valid = gene_df[[plddt_ref_col, plddt_qry_col]].dropna()
        if len(valid) > 0:
            corr = valid[plddt_ref_col].corr(valid[plddt_qry_col])
            r_squared = corr ** 2
            stats.append(("Quality Metrics", "pLDDT Pearson r", f"{corr:.3f}", "Old vs New annotation"))
            stats.append(("Quality Metrics", "pLDDT R-squared", f"{r_squared:.3f}", "Correlation strength"))

    # Save statistics
    stats_df = pd.DataFrame(stats, columns=['Category', 'Metric', 'Value', 'Notes'])
    stats_output = FILTERED_CONFIG["tables_dir"] / "summary_statistics.tsv"
    stats_df.to_csv(stats_output, sep='\t', index=False)

    print(f"\n  Statistics computed: {len(stats)} metrics")
    print(f"  Saved: {stats_output}")

    # Print key statistics
    print("\n  Key Statistics:")
    for _, row in stats_df.iterrows():
        print(f"    {row['Metric']}: {row['Value']} ({row['Notes']})")

    return stats_df


def run_figure_generation(gene_df, transcript_df):
    """
    Run figure generation using PipelineRunner with filtered data.
    """
    print("\n" + "=" * 70)
    print("STEP 5: Generating Figures")
    print("=" * 70)

    # Create config for PipelineRunner
    config = {
        "gene_pav_dir": SCRIPT_DIR,
        "output_dir": FILTERED_CONFIG["output_dir"],
        "transcript_level_tsv": None,  # Will be overridden
        "gene_level_tsv": None,        # Will be overridden
        "psauron_ref": FILTERED_CONFIG["psauron_ref"],
        "psauron_qry": FILTERED_CONFIG["psauron_qry"],
        "proteinx_ref": FILTERED_CONFIG["proteinx_ref"],
        "proteinx_qry": FILTERED_CONFIG["proteinx_qry"],
        "phytopathogen_list": Path("/Users/sadik/Documents/projects/data/disease_research_supported.csv"),
        "fungidb_gene_stats": Path("/Users/sadik/Documents/projects/data/fungidb_v68_gene_stats.tsv"),
        "figure_dpi": 150,
        "figure_format": "png",
    }

    # Create output directory
    config["output_dir"].mkdir(parents=True, exist_ok=True)

    # Initialize runner
    runner = PipelineRunner(config)

    # Override the dataframes with filtered data
    runner._gene_df = gene_df
    runner._transcript_df = transcript_df

    # Track results
    results = []

    # Run all tasks except fungidb_analysis (task 8)
    # Task 6 is Psauron integration which we skip if data already has it
    tasks = [
        ("Task 1: IPR Scatter", runner.task_1_ipr_scatter),
        ("Task 2: Log-Log Scale", runner.task_2_loglog_scale),
        ("Task 2b: Log-Log Class Shapes", runner.task_2b_loglog_class_shapes),
        ("Task 3: Quadrants", runner.task_3_quadrants),
        ("Task 3b: Quadrants Swapped", runner.task_3b_quadrants_swapped),
        ("Task 4: Scenario Barplot", runner.task_4_scenario_barplot),
        ("Task 5: ProteinX", runner.task_5_proteinx),
    ]

    # Add Task 6 (Psauron integration) if data doesn't have psauron yet
    if 'ref_psauron_score_mean' not in gene_df.columns:
        tasks.append(("Task 6: Psauron Integration", runner.task_6_psauron_integration))

    # Add Task 7 (Psauron plots)
    tasks.append(("Task 7: Psauron Plots", runner.task_7_psauron_plots))

    for task_name, task_func in tasks:
        try:
            result = task_func()
            status = "DONE" if result else "SKIPPED"
            results.append((task_name, status, result))
        except Exception as e:
            results.append((task_name, "ERROR", str(e)))
            print(f"  [ERROR] {task_name}: {e}")

    # Print summary
    print("\n" + "-" * 50)
    print("Figure Generation Summary:")
    print("-" * 50)
    for task_name, status, result in results:
        print(f"  [{status}] {task_name}")

    return results


def main():
    """Main entry point."""
    print("\n")
    print("=" * 70)
    print("PAVprot Filtered Analysis: emckmnje=1 Valid Gene Pairs")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Output directory (tables): {FILTERED_CONFIG['tables_dir']}")
    print(f"Output directory (figures): {FILTERED_CONFIG['output_dir']}")
    print("=" * 70)

    # Step 1: Load and filter data
    gene_df, transcript_df = load_and_filter_data()

    # Step 2: Integrate quality metrics (skip if already have psauron columns)
    if 'ref_psauron_score_mean' not in gene_df.columns:
        gene_df, transcript_df = integrate_quality_metrics(gene_df, transcript_df)
    else:
        print("\n" + "=" * 70)
        print("STEP 2: Quality Metrics Already Integrated")
        print("=" * 70)
        print("  Psauron and pLDDT data already present in loaded file")

    # Step 3: Save filtered data
    save_filtered_data(gene_df, transcript_df)

    # Step 4: Compute statistics
    compute_statistics(gene_df)

    # Step 5: Generate figures
    run_figure_generation(gene_df, transcript_df)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"\nOutput locations:")
    print(f"  Tables: {FILTERED_CONFIG['tables_dir']}")
    print(f"  Figures: {FILTERED_CONFIG['output_dir']}")
    print("\nNext steps:")
    print("  1. Review generated figures in figures_out/120126_out/")
    print("  2. Update narrative report with filtered statistics")
    print("  3. Commit changes to git")


if __name__ == "__main__":
    main()
