"""
Alignment plots for PAVprot results.

Generates scatter plots for BBH pident vs coverage,
and histograms for pairwise alignment metrics.
"""

from pathlib import Path
from typing import List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


def plot_bbh_scatter(bbh_file: str, plots_dir: Path) -> List[str]:
    """
    Generate BBH pident vs coverage scatter plot.

    Args:
        bbh_file: Path to BBH results TSV
        plots_dir: Output directory

    Returns:
        List of generated file paths
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for plotting")
        return []

    generated_files = []

    df = pd.read_csv(bbh_file, sep='\t')

    # Check for required columns
    pident_col = None
    cov_col = None

    for col in ['avg_pident', 'pident', 'bbh_avg_pident']:
        if col in df.columns:
            pident_col = col
            break

    for col in ['avg_coverage', 'coverage', 'bbh_avg_coverage', 'qcovhsp']:
        if col in df.columns:
            cov_col = col
            break

    if pident_col is None or cov_col is None:
        logger.warning(f"BBH file missing pident/coverage columns. Found: {df.columns.tolist()}")
        return []

    # Filter valid data
    plot_df = df[[pident_col, cov_col]].dropna()
    plot_df = plot_df[(plot_df[pident_col] > 0) & (plot_df[cov_col] > 0)]

    if len(plot_df) == 0:
        logger.warning("No valid BBH data to plot")
        return []

    # Create scatter plot
    fig, ax = plt.subplots(figsize=(10, 8))

    if HAS_SEABORN:
        sns.scatterplot(
            data=plot_df,
            x=cov_col,
            y=pident_col,
            alpha=0.6,
            s=30,
            ax=ax
        )
    else:
        ax.scatter(
            plot_df[cov_col],
            plot_df[pident_col],
            alpha=0.6,
            s=30
        )

    ax.set_xlabel('Coverage (%)', fontsize=12)
    ax.set_ylabel('Percent Identity (%)', fontsize=12)
    ax.set_title('Bidirectional Best Hits: Identity vs Coverage', fontsize=14, fontweight='bold')

    # Add reference lines
    ax.axhline(y=90, color='green', linestyle='--', alpha=0.5, label='90% identity')
    ax.axhline(y=50, color='orange', linestyle='--', alpha=0.5, label='50% identity')
    ax.axvline(x=80, color='blue', linestyle='--', alpha=0.5, label='80% coverage')

    ax.legend(loc='lower right')
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 105)

    # Add count annotation
    ax.text(0.02, 0.98, f'n = {len(plot_df):,}',
            transform=ax.transAxes, ha='left', va='top',
            fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    output_file = plots_dir / 'bbh_scatter.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    generated_files.append(str(output_file))
    logger.info(f"Saved: {output_file}")

    return generated_files


def plot_alignment_metrics(transcript_file: str, plots_dir: Path) -> List[str]:
    """
    Generate alignment metric histograms from transcript-level data.

    Args:
        transcript_file: Path to transcript-level TSV
        plots_dir: Output directory

    Returns:
        List of generated file paths
    """
    if not HAS_MATPLOTLIB:
        return []

    generated_files = []

    df = pd.read_csv(transcript_file, sep='\t')

    # Plot pident distribution
    pident_col = None
    for col in ['pident', 'pairwise_identity']:
        if col in df.columns:
            pident_col = col
            break

    if pident_col:
        pident_data = df[pident_col].dropna()
        pident_data = pident_data[pident_data > 0]

        if len(pident_data) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))

            ax.hist(pident_data, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
            ax.set_xlabel('Percent Identity (%)', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title('Distribution of Alignment Identity', fontsize=14, fontweight='bold')

            # Add statistics
            mean_val = pident_data.mean()
            median_val = pident_data.median()
            ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.1f}%')
            ax.axvline(median_val, color='green', linestyle='--', label=f'Median: {median_val:.1f}%')
            ax.legend()

            ax.text(0.02, 0.98, f'n = {len(pident_data):,}',
                    transform=ax.transAxes, ha='left', va='top',
                    fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

            plt.tight_layout()

            output_file = plots_dir / 'pident_histogram.png'
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close()
            generated_files.append(str(output_file))
            logger.info(f"Saved: {output_file}")

    # Plot coverage distribution
    cov_col = None
    for col in ['qcovhsp', 'pairwise_coverage_old', 'coverage']:
        if col in df.columns:
            cov_col = col
            break

    if cov_col:
        cov_data = df[cov_col].dropna()
        cov_data = cov_data[cov_data > 0]

        if len(cov_data) > 0:
            fig, ax = plt.subplots(figsize=(10, 6))

            ax.hist(cov_data, bins=50, color='coral', edgecolor='black', alpha=0.7)
            ax.set_xlabel('Coverage (%)', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title('Distribution of Query Coverage', fontsize=14, fontweight='bold')

            mean_val = cov_data.mean()
            median_val = cov_data.median()
            ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.1f}%')
            ax.axvline(median_val, color='green', linestyle='--', label=f'Median: {median_val:.1f}%')
            ax.legend()

            plt.tight_layout()

            output_file = plots_dir / 'coverage_histogram.png'
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close()
            generated_files.append(str(output_file))
            logger.info(f"Saved: {output_file}")

    return generated_files
