#!/usr/bin/env python3
"""
Psauron Score Distribution Comparison Plots

Generates plots comparing Psauron score distributions between
Old annotation (FungiDB v68) and New annotation (NCBI RefSeq),
similar to proteinx_comparison.png format.

Generates two versions:
1. All unfiltered gene pairs
2. emckmnje=1 filtered gene pairs (validated matches)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List

# Configuration
GENE_LEVEL_ALL = Path("output/figures_out/120126_all_out/gene_level_with_psauron.tsv")
GENE_LEVEL_FILTERED = Path("output/120126_out/gene_level_emckmnje1.tsv")
OUTPUT_DIR = Path("output/figures_out/120126_all_out")
FIGURE_DPI = 300

# Column name mapping (ref=NCBI=New, qry=FungiDB=Old)
# Support both old naming (ref/qry) and new naming (new/old)
REF_PSAURON_COL = 'ref_psauron_score_mean'
QRY_PSAURON_COL = 'qry_psauron_score_mean'
ALT_REF_PSAURON_COL = 'new_psauron_score_mean'
ALT_QRY_PSAURON_COL = 'old_psauron_score_mean'


def generate_psauron_comparison_plot(
    df: pd.DataFrame,
    output_path: Path,
    title_suffix: str = "",
    filter_desc: str = "All Gene Pairs"
):
    """
    Generate Psauron distribution comparison plot with two panels:
    - Panel 1: Side-by-side bar chart showing percentage in bins
    - Panel 2: Histogram overlay with density curves

    Args:
        df: DataFrame with ref_psauron and qry_psauron columns
        output_path: Path to save the figure
        title_suffix: Optional suffix for plot title
        filter_desc: Description of data filter applied
    """
    # Extract Psauron scores (ref=NCBI=New, qry=FungiDB=Old)
    ref_psauron = df[REF_PSAURON_COL].dropna()
    qry_psauron = df[QRY_PSAURON_COL].dropna()

    print(f"\n  Data summary:")
    print(f"    New (NCBI RefSeq): n={len(ref_psauron)}, mean={ref_psauron.mean():.3f}, median={ref_psauron.median():.3f}")
    print(f"    Old (FungiDB v68): n={len(qry_psauron)}, mean={qry_psauron.mean():.3f}, median={qry_psauron.median():.3f}")

    # Define Psauron bins (0-1 scale quality levels)
    bins = [0, 0.5, 0.7, 0.9, 1.0]
    labels = ['Low\n(<0.5)', 'Moderate\n(0.5-0.7)', 'Good\n(0.7-0.9)', 'High\n(>0.9)']

    # Bin the data
    ref_binned = pd.cut(ref_psauron, bins=bins, labels=labels, include_lowest=True)
    qry_binned = pd.cut(qry_psauron, bins=bins, labels=labels, include_lowest=True)

    ref_counts = ref_binned.value_counts().reindex(labels, fill_value=0)
    qry_counts = qry_binned.value_counts().reindex(labels, fill_value=0)

    # Calculate percentages
    ref_pct = ref_counts / ref_counts.sum() * 100
    qry_pct = qry_counts / qry_counts.sum() * 100

    # Create figure with two subplots
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # ===== Plot 1: Side-by-side bar chart =====
    x = np.arange(len(labels))
    width = 0.35

    ax1 = axes[0]
    bars1 = ax1.bar(x - width/2, ref_pct, width, label='New (NCBI RefSeq)', color='steelblue')
    bars2 = ax1.bar(x + width/2, qry_pct, width, label='Old (FungiDB v68)', color='coral')

    ax1.set_xlabel('Psauron Quality Level')
    ax1.set_ylabel('Percentage of Genes (%)')
    ax1.set_title(f'Psauron Score Distribution Comparison\n{filter_desc}')
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels)
    ax1.legend()
    ax1.set_ylim(0, max(ref_pct.max(), qry_pct.max()) * 1.15)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f}%', xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)

    # ===== Plot 2: Histogram overlay =====
    ax2 = axes[1]
    ax2.hist(ref_psauron, bins=50, alpha=0.5, label=f'New (NCBI) (n={len(ref_psauron):,})', color='steelblue', density=True)
    ax2.hist(qry_psauron, bins=50, alpha=0.5, label=f'Old (FungiDB) (n={len(qry_psauron):,})', color='coral', density=True)

    # Add threshold lines
    ax2.axvline(x=0.5, color='red', linestyle='--', alpha=0.5, label='Low quality threshold')
    ax2.axvline(x=0.7, color='orange', linestyle='--', alpha=0.5, label='Moderate threshold')
    ax2.axvline(x=0.9, color='green', linestyle='--', alpha=0.5, label='High quality threshold')

    ax2.set_xlabel('Psauron Score')
    ax2.set_ylabel('Density')
    ax2.set_title(f'Psauron Score Density Distribution\n{filter_desc}')
    ax2.set_xlim(0, 1)
    ax2.legend(fontsize=8, loc='upper left')

    plt.tight_layout()

    # Save figure
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")

    # Return statistics for summary
    return {
        'n_new': len(ref_psauron),
        'n_old': len(qry_psauron),
        'mean_new': ref_psauron.mean(),
        'mean_old': qry_psauron.mean(),
        'median_new': ref_psauron.median(),
        'median_old': qry_psauron.median()
    }


def main():
    """Generate Psauron distribution comparison plots."""
    print("=" * 60)
    print("Psauron Score Distribution Comparison")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ===== 1. All unfiltered gene pairs =====
    print("\n[1/2] All Unfiltered Gene Pairs")
    print("-" * 40)

    if GENE_LEVEL_ALL.exists():
        print(f"  Loading: {GENE_LEVEL_ALL}")
        df_all = pd.read_csv(GENE_LEVEL_ALL, sep='\t')
        print(f"    Loaded {len(df_all):,} gene pairs")

        # Check for Psauron columns
        if REF_PSAURON_COL in df_all.columns and QRY_PSAURON_COL in df_all.columns:
            # Filter to rows with valid Psauron scores
            df_valid = df_all.dropna(subset=[REF_PSAURON_COL, QRY_PSAURON_COL])
            print(f"    Valid Psauron pairs: {len(df_valid):,}")

            output_all = OUTPUT_DIR / "psauron_comparison_all.png"
            stats_all = generate_psauron_comparison_plot(
                df_valid,
                output_all,
                filter_desc=f"All Gene Pairs (n={len(df_valid):,})"
            )
        else:
            print("  [ERROR] Psauron columns not found in dataset")
    else:
        print(f"  [ERROR] File not found: {GENE_LEVEL_ALL}")

    # ===== 2. emckmnje=1 filtered gene pairs =====
    print("\n[2/2] emckmnje=1 Filtered Gene Pairs")
    print("-" * 40)

    if GENE_LEVEL_FILTERED.exists():
        print(f"  Loading: {GENE_LEVEL_FILTERED}")
        df_filtered = pd.read_csv(GENE_LEVEL_FILTERED, sep='\t')
        print(f"    Loaded {len(df_filtered):,} gene pairs")

        # Check for Psauron columns
        if REF_PSAURON_COL in df_filtered.columns and QRY_PSAURON_COL in df_filtered.columns:
            # Filter to rows with valid Psauron scores
            df_valid_filtered = df_filtered.dropna(subset=[REF_PSAURON_COL, QRY_PSAURON_COL])
            print(f"    Valid Psauron pairs: {len(df_valid_filtered):,}")

            output_filtered = OUTPUT_DIR / "psauron_comparison_emckmnje1.png"
            stats_filtered = generate_psauron_comparison_plot(
                df_valid_filtered,
                output_filtered,
                filter_desc=f"emckmnje=1 Filtered (n={len(df_valid_filtered):,})"
            )
        else:
            print("  [ERROR] Psauron columns not found in dataset")
    else:
        print(f"  [ERROR] File not found: {GENE_LEVEL_FILTERED}")

    print("\n" + "=" * 60)
    print("Psauron Distribution Plots Complete!")
    print("=" * 60)


def generate_psauron_plots(
    gene_level_file: str,
    output_dir: Path,
    filter_desc: str = "Gene Pairs",
    config: dict = None
) -> List[Path]:
    """
    Generate Psauron distribution plots for CLI integration.

    Args:
        gene_level_file: Path to gene-level TSV with Psauron columns
        output_dir: Directory to save plots
        filter_desc: Description for plot title
        config: Optional configuration (figure_dpi, etc.)

    Returns:
        List of generated plot file paths
    """
    generated_files = []
    config = config or {'figure_dpi': FIGURE_DPI}

    if not Path(gene_level_file).exists():
        print(f"  [ERROR] File not found: {gene_level_file}")
        return generated_files

    print(f"  Loading: {gene_level_file}")
    df = pd.read_csv(gene_level_file, sep='\t')
    print(f"    Loaded {len(df):,} gene pairs")

    # Check for Psauron columns (support both naming conventions)
    ref_col = REF_PSAURON_COL if REF_PSAURON_COL in df.columns else ALT_REF_PSAURON_COL
    qry_col = QRY_PSAURON_COL if QRY_PSAURON_COL in df.columns else ALT_QRY_PSAURON_COL

    if ref_col not in df.columns or qry_col not in df.columns:
        print("  [ERROR] Psauron columns not found in dataset")
        print(f"    Looking for: {REF_PSAURON_COL} or {ALT_REF_PSAURON_COL}")
        print(f"    Looking for: {QRY_PSAURON_COL} or {ALT_QRY_PSAURON_COL}")
        return generated_files

    # Temporarily rename columns if using alternative names
    if ref_col != REF_PSAURON_COL:
        df = df.rename(columns={ref_col: REF_PSAURON_COL, qry_col: QRY_PSAURON_COL})

    # Filter to rows with valid Psauron scores
    df_valid = df.dropna(subset=[REF_PSAURON_COL, QRY_PSAURON_COL])
    print(f"    Valid Psauron pairs: {len(df_valid):,}")

    if len(df_valid) == 0:
        print("  [WARN] No valid Psauron data found")
        return generated_files

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "psauron_comparison.png"
    generate_psauron_comparison_plot(
        df_valid,
        output_path,
        filter_desc=f"{filter_desc} (n={len(df_valid):,})"
    )
    generated_files.append(output_path)

    return generated_files


if __name__ == "__main__":
    main()
