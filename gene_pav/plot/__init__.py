"""
Plotting modules for PAVprot output visualization.

This package provides visualization tools for analyzing PAVprot pipeline output,
including scatter plots, distribution plots, and comparative visualizations.

Modules:
    - config: Plot configuration and styling
    - utils: Shared utility functions for data loading
    - plot_ipr_comparison: InterPro domain comparison plots
    - plot_ipr_gene_level: Gene-level visualization
    - plot_ipr_shapes: Shape-encoded scatter plots
    - plot_ipr_advanced: Advanced visualizations
    - plot_ipr_proportional_bias: Bias analysis plots
    - plot_domain_comparison: Before/after domain comparison
"""

from .config import setup_plotting, get_class_type_palette, get_scenario_palette
from .utils import load_data, load_pavprot_data

__all__ = [
    'setup_plotting',
    'get_class_type_palette',
    'get_scenario_palette',
    'load_data',
    'load_pavprot_data'
]
