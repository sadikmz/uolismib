#!/usr/bin/env python3
"""
Task 2B Loglog Class Shapes

Extracted from: task_2b_loglog_class_shapes
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


def generate_ipr_loglog_class_shapes(gene_df: pd.DataFrame = None, transcript_df: pd.DataFrame = None, output_dir: Path = None, config: dict = None, figure_dpi: int = 150) -> Optional[Path]:
    """
    Generate: test_summary_loglog_scale_class_shapes.png

    Log-log scale scatter with:
    - Shapes = class_type_gene
    - Colors = mapping_type

    Returns:
        Path to output file, or None if skipped
    """
    print("\n[Task 2b] Log-Log Scale Plot with Class Type Shapes")

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

    # Filter and prepare data
    required_cols = [x_col, y_col, 'mapping_type', 'class_type_gene']
    plot_df = df[required_cols].dropna()
    plot_df = plot_df[(plot_df[x_col] > 0) & (plot_df[y_col] > 0)]

    # Colors for mapping types (same as original test_summary_loglog_scale.png - tab10)
    mapping_colors = {
        '1to1': '#1f77b4',      # blue (tab10[0])
        '1to2N': '#ff7f0e',     # orange (tab10[1])
        '1to2N+': '#2ca02c',    # green (tab10[2])
        'Nto1': '#d62728',      # red (tab10[3])
        'complex': '#9467bd',   # purple (tab10[4])
    }

    # Shapes for class types (most common ones)
    class_markers = {
        'a': 'o',           # circle - exact match
        'ackmnj': 's',      # square
        'ackmnje': '^',     # triangle up
        'ckmnj': 'D',       # diamond
        'e': 'v',           # triangle down
        'iy': 'p',          # pentagon
        'o': 'h',           # hexagon
        'pru': '*',         # star
        'sx': 'X',          # X marker
    }

    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot by mapping_type (color) and class_type_gene (shape)
    for mtype in ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']:
        m_mask = plot_df['mapping_type'] == mtype
        if not m_mask.any():
            continue

        color = mapping_colors.get(mtype, 'gray')

        for ctype in plot_df.loc[m_mask, 'class_type_gene'].unique():
            if pd.isna(ctype):
                continue
            c_mask = m_mask & (plot_df['class_type_gene'] == ctype)
            marker = class_markers.get(ctype, 'o')
            # Larger size for 'pru' class type
            size = 80 if ctype == 'pru' else 30

            ax.scatter(
                plot_df.loc[c_mask, x_col],
                plot_df.loc[c_mask, y_col],
                marker=marker,
                c=color,
                alpha=0.6,
                s=size
            )

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
    ax.set_ylabel('New predicted genes total IPR domain length (aa)')
    ax.set_title('Gene pair total IPR domain length (Log-Log scale, Class Type Shapes)')

    # Add diagonal line
    min_val = min(plot_df[x_col].min(), plot_df[y_col].min())
    max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.3)

    # Create separate legends
    from matplotlib.lines import Line2D

    # Legend 1: Colors (Mapping Type)
    color_handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
               markersize=10, label=mapping_type_to_colon(mtype))
        for mtype, color in mapping_colors.items()
        if mtype in plot_df['mapping_type'].values
    ]

    # Legend 2: Shapes (Class Type) - only include those present in data
    shape_handles = [
        Line2D([0], [0], marker=marker, color='w', markerfacecolor='gray',
               markersize=10, label=ctype)
        for ctype, marker in class_markers.items()
        if ctype in plot_df['class_type_gene'].values
    ]

    # Add first legend (colors = mapping type) - inside upper left
    legend1 = ax.legend(handles=color_handles, title='Mapping Type',
                       loc='upper left', bbox_to_anchor=(0.05, 0.95), fontsize=9, framealpha=0.95)
    ax.add_artist(legend1)

    # Add second legend (shapes = class type) - inside lower left
    legend2 = ax.legend(handles=shape_handles, title='Class Type',
                       loc='upper left', bbox_to_anchor=(0.05, 0.50), fontsize=8, framealpha=0.95)

    plt.tight_layout()

    output_path = output_dir / "test_summary_loglog_scale_class_shapes.png"
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")
    return output_path

# =========================================================================
# TASK 3: Quadrants Plot (Presence/Absence Patterns)
# =========================================================================


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
