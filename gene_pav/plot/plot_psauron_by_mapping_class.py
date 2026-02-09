#!/usr/bin/env python3
"""
Task 15 Psauron Dist By Mapping And Class

Extracted from: task_15_psauron_dist_by_mapping_and_class
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


def generate_psauron_by_mapping_class(self):
    """Psauron score distribution by mapping type and class."""
    psauron_gene_file = output_dir / "gene_level_with_psauron.tsv"

    if not psauron_gene_file.exists():
        print("  [SKIP] Psauron gene-level file not found")
        return None

    df = pd.read_csv(psauron_gene_file, sep='\t')

    # Use query column (old annotation psauron scores)
    qry_col = 'qry_psauron_score_mean'

    if qry_col not in df.columns:
        print(f"  [SKIP] Column {qry_col} not found")
        return None

    # Filter to records with scores
    plot_df = df[[qry_col, 'mapping_type', 'class_type_gene']].dropna()

    if len(plot_df) == 0:
        print("  [SKIP] No psauron scores available")
        return None

    # Create figure
    output_path = output_dir / "psauron_distribution_by_mapping_and_class.png"
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    mapping_types = sorted(plot_df['mapping_type'].unique())
    colors = plt.cm.Set3(np.linspace(0, 1, len(plot_df['class_type_gene'].unique())))

    for idx, mapping in enumerate(mapping_types):
        ax = axes[idx // 2, idx % 2]
        subset = plot_df[plot_df['mapping_type'] == mapping]

        for cidx, class_type in enumerate(sorted(subset['class_type_gene'].unique())):
            class_subset = subset[subset['class_type_gene'] == class_type]
            ax.hist(class_subset[qry_col], bins=20, alpha=0.6,
                   label=class_type, color=colors[cidx])

        ax.set_xlabel('Psauron Score')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{mapping} - Psauron Score Distribution')
        ax.legend(fontsize=8)
        ax.set_xlim(0, 1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close()

    print(f"  [DONE] Saved: {output_path}")
    return output_path



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
