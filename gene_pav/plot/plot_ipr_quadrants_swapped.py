#!/usr/bin/env python3
"""
Task 3B Quadrants Swapped

Extracted from: task_3b_quadrants_swapped
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


def generate_ipr_quadrants_swapped(gene_df: pd.DataFrame = None, transcript_df: pd.DataFrame = None, output_dir: Path = None, config: dict = None, figure_dpi: int = 150) -> Optional[Path]:
    """
    Generate: test_summary_quadrants_gene_level_swapped.png

    Same as task_3 but with swapped visual encoding:
    - Colors = Mapping Type (1:1, 1:2N, etc.)
    - Shapes = IPR Domain Pattern (Both, New only, Old only, Neither)

    Returns:
        Path to output file, or None if skipped
    """
    print("\n[Task 3b] Quadrant Plot (Swapped: Colors=MappingType, Shapes=Pattern)")

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

    # Classify into quadrants
    df[x_col] = df[x_col].fillna(0)
    df[y_col] = df[y_col].fillna(0)

    def classify_quadrant(row):
        ref_has = row[x_col] > 0
        qry_has = row[y_col] > 0
        if ref_has and qry_has:
            return 'Both'
        elif ref_has and not qry_has:
            return 'New only'
        elif not ref_has and qry_has:
            return 'Old only'
        else:
            return 'Neither'

    df['quadrant'] = df.apply(classify_quadrant, axis=1)

    # SWAPPED: Shapes for quadrants (IPR Domain Pattern)
    quadrant_markers = {
        'Both': 'o',       # circle
        'New only': 's',   # square
        'Old only': '^',   # triangle
        'Neither': 'X',    # X marker
    }

    # SWAPPED: Colors for mapping types
    mapping_colors = {
        '1to1': 'green',
        '1to2N': 'blue',
        '1to2N+': 'purple',
        'Nto1': 'orange',
        'complex': 'red',
    }

    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot by mapping_type and quadrant (swapped order)
    for mtype in ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']:
        m_mask = df['mapping_type'] == mtype
        if not m_mask.any():
            continue

        for quadrant in df.loc[m_mask, 'quadrant'].unique():
            if pd.isna(quadrant):
                continue
            q_mask = m_mask & (df['quadrant'] == quadrant)
            marker = quadrant_markers.get(quadrant, 'o')
            color = mapping_colors.get(mtype, 'gray')

            ax.scatter(
                df.loc[q_mask, x_col],
                df.loc[q_mask, y_col],
                marker=marker,
                c=color,
                alpha=0.6,
                s=30
            )

    ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
    ax.set_ylabel('New predicted genes total IPR domain length (aa)')
    ax.set_title('Gene-level IPR Domains Presence / Absence Patterns (Swapped Encoding)')

    # Create separate legends
    from matplotlib.lines import Line2D

    # Legend 1: Colors (Mapping Type)
    color_handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
               markersize=10, label=mapping_type_to_colon(mtype))
        for mtype, color in mapping_colors.items()
        if mtype in df['mapping_type'].values
    ]

    # Legend 2: Shapes (IPR Domain Pattern)
    shape_handles = [
        Line2D([0], [0], marker=marker, color='w', markerfacecolor='gray',
               markersize=10, label=quadrant)
        for quadrant, marker in quadrant_markers.items()
        if quadrant in df['quadrant'].values
    ]

    # Add first legend (colors = mapping type) - inside upper left
    legend1 = ax.legend(handles=color_handles, title='Mapping Type',
                       loc='upper left', bbox_to_anchor=(0.05, 0.95), fontsize=9, framealpha=0.95)
    ax.add_artist(legend1)

    # Add second legend (shapes = IPR pattern) - inside lower left
    legend2 = ax.legend(handles=shape_handles, title='IPR Domain Pattern',
                       loc='upper left', bbox_to_anchor=(0.05, 0.50), fontsize=9, framealpha=0.95)

    plt.tight_layout()

    output_path = output_dir / "test_summary_quadrants_gene_level_swapped.png"
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")
    return output_path

# =========================================================================
# TASK 4: Mapping Scenario Bar Plot
# =========================================================================


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
