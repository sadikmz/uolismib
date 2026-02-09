#!/usr/bin/env python3
"""
Task 3 Quadrants

Extracted from: task_3_quadrants
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


def generate_ipr_quadrants(gene_df: pd.DataFrame = None, transcript_df: pd.DataFrame = None, output_dir: Path = None, config: dict = None, figure_dpi: int = 150) -> Optional[Path]:
    """
    Generate: test_summary_quadrants_gene_level.png

    Quadrant plot showing presence/absence patterns.
    Legend: Ref only -> New only, Query only -> Old only
    Separate legends for colors (quadrant) and shapes (mapping_type).

    Returns:
        Path to output file, or None if skipped
    """
    print("\n[Task 3] Quadrant Plot (Presence/Absence Patterns)")

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
    # Fill NaN with 0 for classification
    df[x_col] = df[x_col].fillna(0)
    df[y_col] = df[y_col].fillna(0)

    def classify_quadrant(row):
        ref_has = row[x_col] > 0
        qry_has = row[y_col] > 0
        if ref_has and qry_has:
            return 'Both'
        elif ref_has and not qry_has:
            return 'New only'  # Renamed from 'Ref only'
        elif not ref_has and qry_has:
            return 'Old only'  # Renamed from 'Query only'
        else:
            return 'Neither'

    df['quadrant'] = df.apply(classify_quadrant, axis=1)

    # Define marker shapes for mapping types
    markers = {
        '1to1': 'o',
        '1to2N': 's',
        '1to2N+': '^',
        'Nto1': 'D',
        'complex': 'X',
    }

    # Colors for quadrants
    quadrant_colors = {
        'Both': 'green',
        'New only': 'blue',
        'Old only': 'orange',
        'Neither': 'red',
    }

    fig, ax = plt.subplots(figsize=(12, 8))

    # Plot by quadrant and mapping_type
    for quadrant in ['Both', 'New only', 'Old only', 'Neither']:
        q_mask = df['quadrant'] == quadrant
        if not q_mask.any():
            continue

        for mtype in df.loc[q_mask, 'mapping_type'].unique():
            if pd.isna(mtype):
                continue
            m_mask = q_mask & (df['mapping_type'] == mtype)
            marker = markers.get(mtype, 'o')

            ax.scatter(
                df.loc[m_mask, x_col],
                df.loc[m_mask, y_col],
                marker=marker,
                c=quadrant_colors[quadrant],
                alpha=0.6,
                s=30
            )

    ax.set_xlabel('Old predicted genes total IPR domain length (aa)')
    ax.set_ylabel('New predicted genes total IPR domain length (aa)')
    ax.set_title('Gene-level IPR Domains Presence / Absence Patterns')

    # Create separate legends for colors and shapes
    from matplotlib.lines import Line2D

    # Legend 1: Colors (Quadrant/Presence-Absence)
    color_handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
               markersize=10, label=quadrant)
        for quadrant, color in quadrant_colors.items()
        if quadrant in df['quadrant'].values
    ]

    # Legend 2: Shapes (Mapping Type)
    shape_handles = [
        Line2D([0], [0], marker=marker, color='w', markerfacecolor='gray',
               markersize=10, label=mapping_type_to_colon(mtype))
        for mtype, marker in markers.items()
        if mtype in df['mapping_type'].values
    ]

    # Add first legend (colors) - inside upper left
    legend1 = ax.legend(handles=color_handles, title='IPR Domain Pattern',
                       loc='upper left', bbox_to_anchor=(0.05, 0.95), fontsize=9, framealpha=0.95)
    ax.add_artist(legend1)

    # Add second legend (shapes) - inside lower left
    legend2 = ax.legend(handles=shape_handles, title='Mapping Type',
                       loc='upper left', bbox_to_anchor=(0.05, 0.50), fontsize=9, framealpha=0.95)

    plt.tight_layout()

    output_path = output_dir / "test_summary_quadrants_gene_level.png"
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")
    return output_path

# =========================================================================
# TASK 3b: Quadrants Plot (Swapped - Colors=MappingType, Shapes=Pattern)
# =========================================================================


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
