#!/usr/bin/env python3
"""
IPR Scatter Plot by Class Type

Generates scatter plot of gene pair IPR domain lengths colored by class_type_gene.

Output:
- test_summary_by_class_type.png

Note: Extracted from run_pipeline.py task_1_ipr_scatter
"""

from pathlib import Path
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def generate_ipr_scatter_by_class(
    gene_df: pd.DataFrame = None,
    output_dir: Path = None,
    figure_dpi: int = 150
) -> Optional[Path]:
    """
    Generate IPR scatter plot by class type.

    Args:
        gene_df: Gene-level dataframe with IPR domain lengths
        output_dir: Output directory for plot
        figure_dpi: DPI for figure

    Returns:
        Path to output file, or None if skipped
    """
    print("\n[Plot] IPR Domain Length Scatter Plot by Class Type")

    if gene_df is None:
        print("  [SKIP] Gene-level data not available")
        return None

    # Default output directory
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "plots"

    df = gene_df.copy()

    # Check required columns
    x_col = 'ref_total_ipr_domain_length'
    y_col = 'query_total_ipr_domain_length'

    if x_col not in df.columns or y_col not in df.columns:
        print(f"  [SKIP] Required columns not found: {x_col}, {y_col}")
        return None

    # Filter out missing values
    plot_df = df[[x_col, y_col, 'class_type_gene']].dropna()

    if len(plot_df) == 0:
        print("  [SKIP] No valid data")
        return None

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Color by class_type_gene
    class_types = plot_df['class_type_gene'].unique()
    colors = plt.cm.tab10(np.linspace(0, 1, len(class_types)))

    for ctype, color in zip(class_types, colors):
        mask = plot_df['class_type_gene'] == ctype
        ax.scatter(
            plot_df.loc[mask, x_col],
            plot_df.loc[mask, y_col],
            c=[color],
            label=ctype,
            alpha=0.6,
            s=20
        )

    ax.set_xlabel('New annotation total IPR domain length (aa)')
    ax.set_ylabel('Old annotation total IPR domain length (aa)')
    ax.set_title('Gene pair total IPR domain length')
    ax.legend(title='Class Type', loc='upper left', bbox_to_anchor=(0.05, 0.95), framealpha=0.95)

    # Add diagonal line
    max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label='y=x')

    plt.tight_layout()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "test_summary_by_class_type.png"
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        generate_ipr_scatter_by_class(gene_df, Path(out_dir))
