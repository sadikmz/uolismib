#!/usr/bin/env python3
"""
Plotting configuration and setup for PAVprot visualization modules.

This module provides shared configuration and setup functions for all
plotting scripts to ensure consistent styling across visualizations.
"""

import matplotlib.pyplot as plt
import seaborn as sns

# Default plot settings
DEFAULT_DPI = 300
DEFAULT_FIGSIZE = (10, 8)
DEFAULT_STYLE = "whitegrid"

# Color palettes for different plot types
PALETTES = {
    "class_type": {
        "exact_match": "#2ecc71",      # Green
        "contained": "#3498db",         # Blue
        "intron_match": "#9b59b6",      # Purple
        "novel": "#e74c3c",             # Red
        "other": "#95a5a6"              # Gray
    },
    "scenario": {
        "1:1": "#2ecc71",
        "1:many": "#3498db",
        "many:1": "#e74c3c",
        "many:many": "#9b59b6"
    },
    "ipr_status": {
        "both": "#2ecc71",
        "ref_only": "#3498db",
        "query_only": "#e74c3c",
        "neither": "#95a5a6"
    }
}

# Marker styles for scatter plots
MARKERS = {
    "class_type": {
        "exact_match": "o",
        "contained": "s",
        "intron_match": "^",
        "novel": "D",
        "other": "x"
    }
}


def setup_plotting(style: str = DEFAULT_STYLE,
                   dpi: int = DEFAULT_DPI,
                   figsize: tuple = DEFAULT_FIGSIZE) -> None:
    """
    Configure matplotlib and seaborn settings for consistent plotting.

    Args:
        style: Seaborn style name (default: "whitegrid")
        dpi: Figure DPI for both display and saving (default: 300)
        figsize: Default figure size as (width, height) tuple
    """
    sns.set_style(style)
    plt.rcParams['figure.dpi'] = dpi
    plt.rcParams['savefig.dpi'] = dpi
    plt.rcParams['figure.figsize'] = figsize
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['xtick.labelsize'] = 9
    plt.rcParams['ytick.labelsize'] = 9
    plt.rcParams['legend.fontsize'] = 9


def get_class_type_palette():
    """Return color palette for class_type categories"""
    return PALETTES["class_type"]


def get_scenario_palette():
    """Return color palette for scenario categories"""
    return PALETTES["scenario"]


def get_ipr_status_palette():
    """Return color palette for IPR status categories"""
    return PALETTES["ipr_status"]


def get_class_type_markers():
    """Return marker styles for class_type categories"""
    return MARKERS["class_type"]


def save_figure(fig, output_path, formats=None, tight_layout=True):
    """
    Save figure in multiple formats.

    Args:
        fig: matplotlib figure object
        output_path: Base path for output (without extension)
        formats: List of formats to save (default: ['png'])
        tight_layout: Whether to apply tight_layout before saving
    """
    if formats is None:
        formats = ['png']

    if tight_layout:
        fig.tight_layout()

    for fmt in formats:
        fig.savefig(f"{output_path}.{fmt}", format=fmt, bbox_inches='tight')


# Initialize plotting settings when module is imported
setup_plotting()
