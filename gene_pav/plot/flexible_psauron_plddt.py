#!/usr/bin/env python3
"""
Flexible API for Psauron + pLDDT comparison plots.

Refactored version that accepts labels/titles as positional arguments.
No hard-coded 'ref', 'Ref', 'Ref/Query', 'New/Old' terminology.

Usage Example:
    from gene_pav.plot.flexible_psauron_plddt import plot_dual_comparison

    plot_dual_comparison(
        x1_data=valid['score1'],
        y1_data=valid['score2'],
        x1_label='Genome A Scores',
        y1_label='Genome B Scores',
        x2_data=valid['plddt1'],
        y2_data=valid['plddt2'],
        x2_label='Genome A pLDDT',
        y2_label='Genome B pLDDT',
        title1='Score Comparison',
        title2='Confidence Comparison',
        output_path=Path('output/comparison.png')
    )
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from .flexible_api import (
    scatter_comparison_plot,
    colored_scatter_by_category,
    add_regression_line
)


def plot_dual_comparison(
    x1_data: np.ndarray,
    y1_data: np.ndarray,
    x1_label: str,
    y1_label: str,
    x2_data: np.ndarray,
    y2_data: np.ndarray,
    x2_label: str,
    y2_label: str,
    title1: str,
    title2: str,
    output_path: Path,
    figure_dpi: int = 150,
    scatter_color1: str = '#1f77b4',
    scatter_color2: str = '#ff7f0e',
    add_diagonal: bool = True,
    add_regression: bool = True,
    tight_layout: bool = True
) -> Path:
    """
    Create side-by-side scatter plots comparing two datasets.

    Left panel: First metric (x1_label, y1_label)
    Right panel: Second metric (x2_label, y2_label)

    Args:
        x1_data: First metric X-data
        y1_data: First metric Y-data
        x1_label: First metric X label (provided by caller)
        y1_label: First metric Y label (provided by caller)
        x2_data: Second metric X-data
        y2_data: Second metric Y-data
        x2_label: Second metric X label (provided by caller)
        y2_label: Second metric Y label (provided by caller)
        title1: First plot title
        title2: Second plot title
        output_path: Path to save plot
        figure_dpi: DPI for output
        scatter_color1: Color for first scatter
        scatter_color2: Color for second scatter
        add_diagonal: Add y=x reference lines
        add_regression: Add regression lines

    Returns:
        Path to saved plot
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left panel
    scatter_comparison_plot(
        x1_data, y1_data, x1_label, y1_label, title1,
        ax=axes[0], scatter_color=scatter_color1,
        add_diagonal=add_diagonal, add_regression=add_regression
    )

    # Right panel
    scatter_comparison_plot(
        x2_data, y2_data, x2_label, y2_label, title2,
        ax=axes[1], scatter_color=scatter_color2,
        add_diagonal=add_diagonal, add_regression=add_regression
    )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    return output_path


def plot_by_category_dual(
    x1_data: np.ndarray,
    y1_data: np.ndarray,
    x1_label: str,
    y1_label: str,
    x2_data: np.ndarray,
    y2_data: np.ndarray,
    x2_label: str,
    y2_label: str,
    categories: pd.Series,
    title1: str,
    title2: str,
    output_path: Path,
    category_labels: Optional[dict] = None,
    category_colors: Optional[dict] = None,
    figure_dpi: int = 150,
    add_diagonal: bool = True,
    add_regression: bool = True,
    legend_fontsize: int = 8,
    legend_loc: str = 'upper left'
) -> Path:
    """
    Create side-by-side scatter plots colored by category.

    Args:
        x1_data: First metric X-data
        y1_data: First metric Y-data
        x1_label: First metric X label (provided by caller)
        y1_label: First metric Y label (provided by caller)
        x2_data: Second metric X-data
        y2_data: Second metric Y-data
        x2_label: Second metric X label (provided by caller)
        y2_label: Second metric Y label (provided by caller)
        categories: Series with category assignments
        title1: First plot title
        title2: Second plot title
        output_path: Path to save plot
        category_labels: Dict mapping category → display label
        category_colors: Dict mapping category → color
        figure_dpi: DPI for output
        add_diagonal: Add y=x reference lines
        add_regression: Add regression lines
        legend_fontsize: Font size for legend
        legend_loc: Legend location inside plots ('upper left', 'upper right', etc.)

    Returns:
        Path to saved plot
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left panel
    colored_scatter_by_category(
        x1_data, y1_data, categories,
        x1_label, y1_label, title1,
        ax=axes[0], category_labels=category_labels,
        category_colors=category_colors,
        add_diagonal=add_diagonal, add_regression=add_regression,
        legend_fontsize=legend_fontsize, legend_loc=legend_loc
    )

    # Right panel
    colored_scatter_by_category(
        x2_data, y2_data, categories,
        x2_label, y2_label, title2,
        ax=axes[1], category_labels=category_labels,
        category_colors=category_colors,
        add_diagonal=add_diagonal, add_regression=add_regression,
        legend_fontsize=legend_fontsize, legend_loc=legend_loc
    )

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig)

    return output_path
