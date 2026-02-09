#!/usr/bin/env python3
"""
Task 4 Scenario Barplot

Extracted from: task_4_scenario_barplot
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


def generate_scenario_barplot(gene_df: pd.DataFrame = None, transcript_df: pd.DataFrame = None, output_dir: Path = None, config: dict = None, figure_dpi: int = 150) -> Optional[Path]:
    """
    Generate: scenario_barplot.png (New_plot_1)

    Horizontal stacked bar plot of gene pairs by mapping scenario.
    Color partitioned by class_type_gene.
    Also generates non-stacked version.

    Returns:
        Path to output file, or None if skipped
    """
    print("\n[Task 4] Mapping Scenario Bar Plot")

    if gene_df is None:
        print("  [SKIP] Gene-level data not available")
        return None

    df = gene_df.copy()

    if 'scenario' not in df.columns:
        print("  [SKIP] 'scenario' column not found")
        return None

    # Count gene pairs by scenario and class_type_gene
    counts = df.groupby(['scenario', 'class_type_gene']).size().unstack(fill_value=0)

    # Reorder scenarios
    scenario_order = ['E', 'A', 'J', 'B', 'CDI']
    counts = counts.reindex([s for s in scenario_order if s in counts.index])

    # Map scenario letters to 1:N notation for display
    scenario_to_notation = {
        'E': '1:1',
        'A': '1:2N',
        'J': '1:2N+',
        'B': 'N:1',
        'CDI': 'complex',
    }
    counts.index = counts.index.map(lambda x: scenario_to_notation.get(x, x))

    # ===== Stacked version =====
    fig1, ax1 = plt.subplots(figsize=(12, 6))

    counts.plot(kind='barh', stacked=True, ax=ax1, colormap='tab10')

    ax1.set_xlabel('Number of gene pairs')
    ax1.set_ylabel('Mapping Type')
    ax1.set_title('Gene Pairs by Mapping Type (Stacked by Class Type)')
    ax1.legend(title='Class Type', bbox_to_anchor=(1.02, 1), loc='upper left')

    plt.tight_layout()

    output_stacked = output_dir / "scenario_barplot_stacked.png"
    fig1.savefig(output_stacked, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig1)

    print(f"  [DONE] Saved: {output_stacked}")

    # ===== Non-stacked version =====
    fig2, ax2 = plt.subplots(figsize=(10, 6))

    scenario_totals = counts.sum(axis=1)
    scenario_totals.plot(kind='barh', ax=ax2, color='steelblue')

    ax2.set_xlabel('Number of gene pairs')
    ax2.set_ylabel('Mapping Type')
    ax2.set_title('Gene Pairs by Mapping Type')

    # Add count labels
    for i, v in enumerate(scenario_totals):
        ax2.text(v + 50, i, str(int(v)), va='center')

    plt.tight_layout()

    output_simple = output_dir / "scenario_barplot_simple.png"
    fig2.savefig(output_simple, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig2)

    print(f"  [DONE] Saved: {output_simple}")

    return output_stacked

# =========================================================================
# TASK 5: ProteinX Plot
# =========================================================================


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
