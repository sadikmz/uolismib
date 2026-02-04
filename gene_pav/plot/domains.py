"""
InterProScan domain plots for PAVprot results.

Generates comparison plots for IPR domain lengths between
old and new annotations.
"""

from pathlib import Path
from typing import List, Optional
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


def plot_ipr_comparison(
    old_ipr_file: Optional[str],
    new_ipr_file: Optional[str],
    plots_dir: Path
) -> List[str]:
    """
    Generate IPR domain length comparison plots.

    Args:
        old_ipr_file: Path to old annotation domain distribution TSV
        new_ipr_file: Path to new annotation domain distribution TSV
        plots_dir: Output directory

    Returns:
        List of generated file paths
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for plotting")
        return []

    generated_files = []

    # Load available IPR length files
    old_lengths = None
    new_lengths = None

    if old_ipr_file and Path(old_ipr_file).exists():
        old_lengths = _load_ipr_lengths(old_ipr_file)

    if new_ipr_file and Path(new_ipr_file).exists():
        new_lengths = _load_ipr_lengths(new_ipr_file)

    # Generate comparison histogram if both available
    if old_lengths is not None and new_lengths is not None:
        files = _plot_length_comparison(old_lengths, new_lengths, plots_dir)
        generated_files.extend(files)

    # Generate individual histograms
    if old_lengths is not None:
        files = _plot_length_histogram(old_lengths, 'Old Annotation', plots_dir, 'old')
        generated_files.extend(files)

    if new_lengths is not None:
        files = _plot_length_histogram(new_lengths, 'New Annotation', plots_dir, 'new')
        generated_files.extend(files)

    return generated_files


def _load_ipr_lengths(filepath: str) -> Optional[pd.Series]:
    """Load IPR domain lengths from file."""
    try:
        df = pd.read_csv(filepath, sep='\t')

        # Look for length column
        len_col = None
        for col in ['total_iprdom_len', 'total_ipr_domain_length', 'length', 'domain_length']:
            if col in df.columns:
                len_col = col
                break

        if len_col is None:
            # Try domain distribution file format
            if 'length' in df.columns:
                return df['length'].dropna()
            logger.warning(f"No length column found in {filepath}")
            return None

        return df[len_col].dropna()

    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return None


def _plot_length_comparison(
    old_lengths: pd.Series,
    new_lengths: pd.Series,
    plots_dir: Path
) -> List[str]:
    """Generate side-by-side length comparison."""
    generated_files = []

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Old annotation histogram
    axes[0].hist(old_lengths, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    axes[0].set_xlabel('Total IPR Domain Length', fontsize=11)
    axes[0].set_ylabel('Frequency', fontsize=11)
    axes[0].set_title('Old Annotation', fontsize=12, fontweight='bold')
    axes[0].text(0.98, 0.98, f'n = {len(old_lengths):,}\nMean: {old_lengths.mean():.0f}',
                 transform=axes[0].transAxes, ha='right', va='top',
                 fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # New annotation histogram
    axes[1].hist(new_lengths, bins=50, color='coral', edgecolor='black', alpha=0.7)
    axes[1].set_xlabel('Total IPR Domain Length', fontsize=11)
    axes[1].set_ylabel('Frequency', fontsize=11)
    axes[1].set_title('New Annotation', fontsize=12, fontweight='bold')
    axes[1].text(0.98, 0.98, f'n = {len(new_lengths):,}\nMean: {new_lengths.mean():.0f}',
                 transform=axes[1].transAxes, ha='right', va='top',
                 fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    fig.suptitle('IPR Domain Length Distribution Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()

    output_file = plots_dir / 'ipr_length_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    generated_files.append(str(output_file))
    logger.info(f"Saved: {output_file}")

    # Generate overlay histogram
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(old_lengths, bins=50, alpha=0.5, label=f'Old (n={len(old_lengths):,})', color='steelblue')
    ax.hist(new_lengths, bins=50, alpha=0.5, label=f'New (n={len(new_lengths):,})', color='coral')

    ax.set_xlabel('Total IPR Domain Length', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('IPR Domain Length Distribution Overlay', fontsize=14, fontweight='bold')
    ax.legend()

    plt.tight_layout()

    output_file = plots_dir / 'ipr_length_overlay.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    generated_files.append(str(output_file))
    logger.info(f"Saved: {output_file}")

    return generated_files


def _plot_length_histogram(
    lengths: pd.Series,
    title: str,
    plots_dir: Path,
    prefix: str
) -> List[str]:
    """Generate single length histogram."""
    generated_files = []

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(lengths, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Total IPR Domain Length', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(f'IPR Domain Length Distribution - {title}', fontsize=14, fontweight='bold')

    # Add statistics
    mean_val = lengths.mean()
    median_val = lengths.median()
    ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.0f}')
    ax.axvline(median_val, color='green', linestyle='--', label=f'Median: {median_val:.0f}')
    ax.legend()

    ax.text(0.98, 0.98, f'n = {len(lengths):,}',
            transform=ax.transAxes, ha='right', va='top',
            fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    output_file = plots_dir / f'ipr_length_{prefix}.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    generated_files.append(str(output_file))
    logger.info(f"Saved: {output_file}")

    return generated_files
