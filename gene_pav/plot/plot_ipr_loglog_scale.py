#!/usr/bin/env python3
"""
Task 2 Loglog Scale

Extracted from: task_2_loglog_scale
Moved to plot module for production use.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def mapping_type_to_colon(mapping_type: str) -> str:
    """Convert mapping_type to colon notation (e.g., '1to1' -> '1:1')."""
    return mapping_type.replace('to', ':')


def generate_ipr_loglog_scale(gene_df: pd.DataFrame = None, transcript_df: pd.DataFrame = None, output_dir: Path = None, config: dict = None, figure_dpi: int = 150) -> Optional[Path]:
    """
    Generate: test_summary_loglog_scale.png

    Log-log scale scatter with different shapes by mapping_type.
    Legend uses ':' notation (1:1, 1:2N, etc.)

    Returns:
        Path to output file, or None if skipped
    """
    print("\n[Task 2] Log-Log Scale Plot with Mapping Type Shapes")

    if gene_df is None:
        print("  [SKIP] Gene-level data not available")
        return None

    # Default output directory
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "plots"

    df = gene_df.copy()

    x_col = 'ref_total_ipr_domain_length'
    y_col = 'query_total_ipr_domain_length'

    if x_col not in df.columns or y_col not in df.columns:
        print(f"  [SKIP] Required columns not found: {x_col}, {y_col}")
        return None

    # Filter and prepare data (add small value for log scale)
    plot_df = df[[x_col, y_col, 'mapping_type']].dropna()
    plot_df = plot_df[(plot_df[x_col] > 0) & (plot_df[y_col] > 0)]

    # Define marker shapes for mapping types
    markers = {
        '1to1': 'o',      # circle
        '1to2N': 's',     # square
        '1to2N+': '^',    # triangle up
        'Nto1': 'D',      # diamond
        'complex': 'X',   # X marker
    }

    fig, ax = plt.subplots(figsize=(10, 8))

    for mtype in plot_df['mapping_type'].unique():
        mask = plot_df['mapping_type'] == mtype
        marker = markers.get(mtype, 'o')
        label = mapping_type_to_colon(mtype)  # Convert to ':' notation

        ax.scatter(
            plot_df.loc[mask, x_col],
            plot_df.loc[mask, y_col],
            marker=marker,
            label=label,
            alpha=0.6,
            s=30
        )

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
    ax.set_ylabel('New predicted genes total IPR domain length (aa)')
    ax.set_title('Gene pair total IPR domain length (Log-Log scale plot)')
    ax.legend(title='Mapping Type', loc='upper left', bbox_to_anchor=(0.05, 0.95), framealpha=0.95)

    # Add diagonal line
    min_val = min(plot_df[x_col].min(), plot_df[y_col].min())
    max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.3)

    plt.tight_layout()

    output_path = output_dir / "test_summary_loglog_scale.png"
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")
    return output_path

# =========================================================================
# TASK 2b: Log-Log Scale Plot with Class Type Shapes
# =========================================================================


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
