#!/usr/bin/env python3
"""
Flexible API for plot generation - accepts labels/titles as positional arguments.

This module ensures no hard-coded 'ref', 'Ref', 'qry', 'Qry' terminology.
All labels, titles, and identifiers are provided by callers.

PRINCIPLE:
  Data inputs + metadata (labels) as positional arguments
  → Same functions work for any data source/type
  → No assumptions about data origin embedded in code
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy import stats
from typing import Optional, Tuple, Callable


def add_regression_line(
    ax,
    x_data: np.ndarray,
    y_data: np.ndarray,
    line_color: str = 'red',
    line_style: str = '-',
    line_alpha: float = 0.8,
    text_position: Tuple[float, float] = (0.95, 0.05)
) -> None:
    """
    Add regression line with equation and R² to plot.

    Args:
        ax: Matplotlib axis
        x_data: X-axis data
        y_data: Y-axis data
        line_color: Color for regression line
        line_style: Line style (-, --, :, etc)
        line_alpha: Alpha transparency
        text_position: (x, y) for equation text placement (0-1 normalized coords)
    """
    # Remove NaN values
    mask = ~(np.isnan(x_data) | np.isnan(y_data))
    x_clean, y_clean = x_data[mask], y_data[mask]

    if len(x_clean) < 2:
        return

    slope, intercept, r_value, _, _ = stats.linregress(x_clean, y_clean)

    # Plot regression line
    x_line = np.array([x_clean.min(), x_clean.max()])
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color=line_color, linestyle=line_style,
            linewidth=2, alpha=line_alpha)

    # Add equation text
    eq_text = f'y = {slope:.3f}x + {intercept:.3f}\nR² = {r_value**2:.3f}'
    ax.text(text_position[0], text_position[1], eq_text,
            transform=ax.transAxes, fontsize=8, ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))


def scatter_comparison_plot(
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    ax: Optional[plt.Axes] = None,
    scatter_color: str = '#1f77b4',
    scatter_alpha: float = 0.3,
    scatter_size: int = 15,
    add_diagonal: bool = True,
    add_regression: bool = True,
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None
) -> plt.Axes:
    """
    Create scatter plot comparing two datasets.

    Args:
        x_data: X-axis data
        y_data: Y-axis data
        x_label: X-axis label (provided by caller)
        y_label: Y-axis label (provided by caller)
        title: Plot title (provided by caller)
        ax: Matplotlib axis (created if None)
        scatter_color: Color for scatter points
        scatter_alpha: Transparency for points
        scatter_size: Point size
        add_diagonal: Add y=x reference line
        add_regression: Add regression line
        xlim: X-axis limits
        ylim: Y-axis limits

    Returns:
        Matplotlib axis with plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))

    # Scatter plot
    ax.scatter(x_data, y_data, alpha=scatter_alpha, s=scatter_size,
              c=scatter_color)

    # Diagonal reference line
    if add_diagonal:
        x_min = np.nanmin(x_data)
        x_max = np.nanmax(x_data)
        ax.plot([x_min, x_max], [x_min, x_max], 'k--', alpha=0.3, label='y=x')

    # Regression line
    if add_regression:
        add_regression_line(ax, x_data, y_data, line_color='red')

    # Labels and title
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    # Limits
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)

    return ax


def colored_scatter_by_category(
    x_data: np.ndarray,
    y_data: np.ndarray,
    categories: pd.Series,
    x_label: str,
    y_label: str,
    title: str,
    ax: Optional[plt.Axes] = None,
    category_labels: Optional[dict] = None,
    category_colors: Optional[dict] = None,
    add_diagonal: bool = True,
    add_regression: bool = True,
    xlim: Optional[Tuple[float, float]] = None,
    ylim: Optional[Tuple[float, float]] = None,
    legend_fontsize: int = 8,
    legend_loc: str = 'upper left'
) -> plt.Axes:
    """
    Create scatter plot with points colored by category.

    Args:
        x_data: X-axis data
        y_data: Y-axis data
        categories: Series with category assignments
        x_label: X-axis label (provided by caller)
        y_label: Y-axis label (provided by caller)
        title: Plot title (provided by caller)
        ax: Matplotlib axis (created if None)
        category_labels: Dict mapping category → display label
        category_colors: Dict mapping category → color
        add_diagonal: Add y=x reference line
        add_regression: Add regression line
        xlim: X-axis limits
        ylim: Y-axis limits
        legend_fontsize: Font size for legend
        legend_loc: Legend location inside plot ('upper left', 'upper right', etc.)

    Returns:
        Matplotlib axis with plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))

    # Get unique categories
    unique_cats = categories.unique()

    # Default labels and colors
    if category_labels is None:
        category_labels = {cat: str(cat) for cat in unique_cats}
    if category_colors is None:
        color_map = plt.cm.tab10(np.linspace(0, 1, len(unique_cats)))
        category_colors = {cat: color_map[i] for i, cat in enumerate(unique_cats)}

    # Plot each category
    for cat in unique_cats:
        mask = categories == cat
        subset_x = x_data[mask]
        subset_y = y_data[mask]

        ax.scatter(subset_x, subset_y, alpha=0.4, s=20,
                  c=[category_colors.get(cat, 'gray')],
                  label=f'{category_labels[cat]} (n={np.sum(mask)})')

    # Diagonal reference line
    if add_diagonal:
        x_min = np.nanmin(x_data)
        x_max = np.nanmax(x_data)
        ax.plot([x_min, x_max], [x_min, x_max], 'k--', alpha=0.3)

    # Regression line (using all data)
    if add_regression:
        add_regression_line(ax, x_data, y_data, line_color='red')

    # Labels and title
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    # Legend (inside plot area, overlapping data)
    ax.legend(fontsize=legend_fontsize, loc='lower right', framealpha=0.95)

    # Limits
    if xlim:
        ax.set_xlim(xlim)
    if ylim:
        ax.set_ylim(ylim)

    return ax


def distribution_comparison_plot(
    x_data: np.ndarray,
    y_data: np.ndarray,
    x_label: str,
    y_label: str,
    title: str,
    ax: Optional[plt.Axes] = None,
    x_color: str = 'steelblue',
    y_color: str = 'coral',
    x_name: str = 'Dataset 1',
    y_name: str = 'Dataset 2',
    bins: int = 50,
    density: bool = True,
    alpha: float = 0.5,
    threshold_lines: Optional[list] = None
) -> plt.Axes:
    """
    Create overlaid histogram comparing two distributions.

    Args:
        x_data: First dataset
        y_data: Second dataset
        x_label: X-axis label (provided by caller)
        y_label: Y-axis label (provided by caller)
        title: Plot title (provided by caller)
        ax: Matplotlib axis (created if None)
        x_color: Color for first histogram
        y_color: Color for second histogram
        x_name: Display name for first dataset
        y_name: Display name for second dataset
        bins: Number of histogram bins
        density: Normalize to density
        alpha: Transparency
        threshold_lines: List of (value, color, label) tuples for vertical lines
            (legend positioned inside plot area)

    Returns:
        Matplotlib axis with plot
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(8, 6))

    # Histograms
    ax.hist(x_data.dropna() if isinstance(x_data, pd.Series) else x_data,
           bins=bins, alpha=alpha, label=f'{x_name} (n={len(x_data)})',
           color=x_color, density=density)
    ax.hist(y_data.dropna() if isinstance(y_data, pd.Series) else y_data,
           bins=bins, alpha=alpha, label=f'{y_name} (n={len(y_data)})',
           color=y_color, density=density)

    # Threshold lines (provided by caller)
    if threshold_lines:
        for value, color, label in threshold_lines:
            ax.axvline(x=value, color=color, linestyle='--', alpha=0.5,
                      label=label)

    # Labels and title
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    # Legend (inside plot area, overlapping data)
    ax.legend(fontsize=8, loc='lower left', framealpha=0.95)

    return ax
