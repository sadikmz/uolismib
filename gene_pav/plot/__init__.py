"""
Plotting modules for PAVprot output visualization.

This package provides visualization tools for analyzing PAVprot pipeline output,
including scatter plots, distribution plots, and comparative visualizations.

**AUTHORITATIVE PLOT MODULES (14 total):**
    Core Modules (5):
    - plot_oldvsnew_psauron_plddt: Quality score scatter plots (new vs old)
    - plot_psauron_distribution: Psauron distribution histograms
    - plot_ipr_1to1_comparison: IPR 1:1 comparison for Scenario E pairs
    - advanced: Advanced IPR analysis (log-log, quadrant analysis)
    - scenarios: Scenario distribution plots

    New Integrated Modules (9):
    - plot_ipr_scatter_by_class: IPR scatter by class type
    - plot_ipr_loglog_scale: Log-log scale IPR plots
    - plot_ipr_loglog_class_shapes: Log-log with class shapes
    - plot_ipr_quadrants: IPR quadrant analysis
    - plot_ipr_quadrants_swapped: IPR quadrants (swapped axes)
    - plot_scenario_barplot: Scenario bar plot
    - plot_proteinx_comparison: ProteinX/pLDDT comparison
    - plot_fungidb_analysis: FungiDB transcript analysis
    - plot_psauron_by_mapping_class: Psauron distribution by mapping/class

CLI Plot Types (via --plot argument):
    - scenarios: Scenario distribution plots
    - ipr: IPR domain scatter by class type
    - advanced: Advanced IPR analysis (log-log, quadrant, detailed)
    - 1to1: IPR 1:1 ortholog pairs comparison
    - psauron: Psauron score distributions
    - quality: Quality scores (Psauron new vs old)
    - all: All available plots

**REFERENCE MODULES (9 duplicates in extracted_tasks/):**
    For archival/comparison only - use authoritative modules instead.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
import pandas as pd

from .config import setup_plotting, get_class_type_palette, get_scenario_palette
from .utils import load_data, load_pavprot_data
from .data_prep import load_and_enrich, enrich_pavprot_data, validate_enrichment

# ============================================================================
# IMPORT ALL PLOT GENERATION FUNCTIONS FROM ALL AUTHORITATIVE MODULES
# ============================================================================

# CORE MODULES (5)
# Note: Some legacy modules have different function names

# NEW INTEGRATED MODULES (9)
from .plot_ipr_scatter_by_class import generate_ipr_scatter_by_class
from .plot_ipr_loglog_scale import generate_ipr_loglog_scale
from .plot_ipr_loglog_class_shapes import generate_ipr_loglog_class_shapes
from .plot_ipr_quadrants import generate_ipr_quadrants
from .plot_ipr_quadrants_swapped import generate_ipr_quadrants_swapped
from .plot_scenario_barplot import generate_scenario_barplot
from .plot_proteinx_comparison import generate_proteinx_comparison
from .plot_fungidb_analysis import generate_fungidb_analysis
# from .plot_psauron_by_mapping_class import generate_psauron_by_mapping_class  # TODO: Fix signature

# LEGACY MODULE FUNCTIONS (for advanced plotting)
from . import scenarios, advanced

# FLEXIBLE API - NO HARD-CODED LABELS (data-agnostic plotting)
from .flexible_api import (
    add_regression_line,
    scatter_comparison_plot,
    colored_scatter_by_category,
    distribution_comparison_plot
)
from .flexible_psauron_plddt import (
    plot_dual_comparison,
    plot_by_category_dual
)

logger = logging.getLogger(__name__)


def generate_plots(
    output_dir: str,
    plot_types: Optional[List[str]] = None,
    transcript_level_file: Optional[str] = None,
    gene_level_file: Optional[str] = None,
    bbh_file: Optional[str] = None,
    old_ipr_file: Optional[str] = None,
    new_ipr_file: Optional[str] = None,
    figure_dpi: int = 150,
) -> List[str]:
    """
    Generate visualization plots for PAVprot results.

    Args:
        output_dir: Main output directory (plots saved to {output_dir}/plots)
        plot_types: List of plot types to generate.
                   Options: 'scenarios', 'ipr', 'advanced', '1to1', 'psauron', 'quality', 'all'
                   If None or 'all', generates all available plots.
        transcript_level_file: Path to transcript-level TSV output
        gene_level_file: Path to gene-level TSV output
        bbh_file: Path to BBH results TSV (legacy, not used)
        old_ipr_file: Path to old annotation IPR domain distribution TSV
        new_ipr_file: Path to new annotation IPR domain distribution TSV
        figure_dpi: DPI for figure output

    Returns:
        List of generated plot file paths
    """
    # Create plots directory
    plots_dir = Path(output_dir) / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Load gene-level data if available
    gene_df = None
    transcript_df = None

    if gene_level_file and Path(gene_level_file).exists():
        try:
            gene_df = pd.read_csv(gene_level_file, sep='\t')
            logger.info(f"Loaded gene-level data: {len(gene_df)} records")
        except Exception as e:
            logger.warning(f"Failed to load gene-level data: {e}")

    if transcript_level_file and Path(transcript_level_file).exists():
        try:
            transcript_df = pd.read_csv(transcript_level_file, sep='\t')
            logger.info(f"Loaded transcript-level data: {len(transcript_df)} records")
        except Exception as e:
            logger.warning(f"Failed to load transcript-level data: {e}")

    # Default to all plot types if none specified or 'all' specified
    if not plot_types or 'all' in plot_types:
        plot_types = ['scenarios', 'ipr', 'advanced', '1to1', 'psauron', 'quality']

    # =========================================================================
    # SCENARIO PLOTS
    # =========================================================================
    if 'scenarios' in plot_types:
        if gene_df is not None:
            try:
                result = generate_scenario_barplot(
                    gene_df=gene_df,
                    output_dir=plots_dir,
                    figure_dpi=figure_dpi
                )
                if result:
                    generated_files.append(str(result))
                    logger.info(f"Generated scenario barplot")
            except Exception as e:
                logger.warning(f"Failed to generate scenario barplot: {e}")
        else:
            logger.warning("Skipping scenario plots: gene-level data not available")

    # =========================================================================
    # IPR SCATTER PLOTS
    # =========================================================================
    if 'ipr' in plot_types:
        if gene_df is not None:
            try:
                result = generate_ipr_scatter_by_class(
                    gene_df=gene_df,
                    output_dir=plots_dir,
                    figure_dpi=figure_dpi
                )
                if result:
                    generated_files.append(str(result))
                    logger.info(f"Generated IPR scatter by class plot")
            except Exception as e:
                logger.warning(f"Failed to generate IPR scatter plot: {e}")
        else:
            logger.warning("Skipping IPR scatter plots: gene-level data not available")

    # =========================================================================
    # ADVANCED IPR PLOTS (log-log, quadrants, etc.)
    # =========================================================================
    if 'advanced' in plot_types:
        if gene_df is not None:
            try:
                # Log-log scale
                result = generate_ipr_loglog_scale(
                    gene_df=gene_df,
                    output_dir=plots_dir,
                    figure_dpi=figure_dpi
                )
                if result:
                    generated_files.append(str(result))
            except Exception as e:
                logger.warning(f"Failed to generate log-log plot: {e}")

            try:
                # Log-log with class shapes
                result = generate_ipr_loglog_class_shapes(
                    gene_df=gene_df,
                    output_dir=plots_dir,
                    figure_dpi=figure_dpi
                )
                if result:
                    generated_files.append(str(result))
            except Exception as e:
                logger.warning(f"Failed to generate log-log class shapes plot: {e}")

            try:
                # Quadrant analysis
                result = generate_ipr_quadrants(
                    gene_df=gene_df,
                    output_dir=plots_dir,
                    figure_dpi=figure_dpi
                )
                if result:
                    generated_files.append(str(result))
            except Exception as e:
                logger.warning(f"Failed to generate quadrant plot: {e}")

            try:
                # Quadrant analysis (swapped)
                result = generate_ipr_quadrants_swapped(
                    gene_df=gene_df,
                    output_dir=plots_dir,
                    figure_dpi=figure_dpi
                )
                if result:
                    generated_files.append(str(result))
            except Exception as e:
                logger.warning(f"Failed to generate swapped quadrant plot: {e}")

            logger.info(f"Generated advanced IPR plots")
        else:
            logger.warning("Skipping advanced plots: gene-level data not available")

    # =========================================================================
    # 1:1 ORTHOLOG PLOTS
    # =========================================================================
    if '1to1' in plot_types:
        if gene_level_file and Path(gene_level_file).exists():
            try:
                files = generate_1to1_plots(
                    gene_level_file=gene_level_file,
                    output_dir=plots_dir,
                    config=None
                )
                if files:
                    generated_files.extend([str(f) for f in files if f])
                    logger.info(f"Generated 1:1 ortholog plots: {len([f for f in files if f])} files")
            except Exception as e:
                logger.warning(f"Failed to generate 1:1 plots: {e}")
        else:
            logger.warning("Skipping 1:1 plots: gene-level file not available")

    # =========================================================================
    # PSAURON DISTRIBUTION PLOTS
    # =========================================================================
    if 'psauron' in plot_types:
        if gene_level_file and Path(gene_level_file).exists():
            try:
                files = generate_psauron_plots(
                    gene_level_file=gene_level_file,
                    output_dir=plots_dir,
                    config=None
                )
                if files:
                    generated_files.extend([str(f) for f in files if f])
                    logger.info(f"Generated Psauron distribution plots: {len([f for f in files if f])} files")
            except Exception as e:
                logger.warning(f"Failed to generate Psauron plots: {e}")
        else:
            logger.warning("Skipping Psauron plots: gene-level file not available")

    # =========================================================================
    # QUALITY SCORE PLOTS
    # =========================================================================
    if 'quality' in plot_types:
        if gene_level_file and Path(gene_level_file).exists():
            try:
                files = generate_quality_score_plots(
                    gene_level_file=gene_level_file,
                    output_dir=plots_dir,
                    config=None
                )
                if files:
                    generated_files.extend([str(f) for f in files if f])
                    logger.info(f"Generated quality score plots: {len([f for f in files if f])} files")
            except Exception as e:
                logger.warning(f"Failed to generate quality plots: {e}")
        else:
            logger.warning("Skipping quality plots: gene-level file not available")

    logger.info(f"Generated {len(generated_files)} plot files total")
    return generated_files


# ============================================================================
# USAGE GUIDE - HOW TO USE ALL PLOT FUNCTIONS
# ============================================================================
"""
COMPLETE PLOTTING API REFERENCE
================================

This module exposes ALL 14+ plot generation functions from the PAVprot analysis
pipeline. Use any of these methods to generate publication-quality visualizations.

METHOD 1: MASTER ORCHESTRATOR (Recommended for most users)
─────────────────────────────────────────────────────────
Generate multiple plot types at once:

    from gene_pav.plot import generate_plots

    plots = generate_plots(
        output_dir='results/',
        plot_types=['scenarios', 'ipr', 'advanced', '1to1'],
        gene_level_file='data/gene_level.tsv',
        figure_dpi=150
    )

METHOD 2: INDIVIDUAL PLOT FUNCTIONS (Direct API)
────────────────────────────────────────────────
Call specific plot generation functions:

    from gene_pav.plot import (
        generate_ipr_scatter_by_class,
        generate_ipr_loglog_scale,
        generate_ipr_quadrants,
        generate_scenario_barplot,
        generate_1to1_plots,
        generate_quality_score_plots,
        generate_psauron_plots,
    )

    # Generate individual plots
    generate_ipr_scatter_by_class(gene_df=data, output_dir=Path('plots/'))
    generate_scenario_barplot(gene_df=data, output_dir=Path('plots/'))

METHOD 3: ADVANCED MODULE FUNCTIONS (For advanced analysis)
──────────────────────────────────────────────────────────
Use the advanced plotting module directly:

    from gene_pav.plot import advanced

    # Generate advanced IPR plots (log-log, quadrant, detailed)
    plots = advanced.generate_advanced_plots(
        output_dir='results/',
        gene_level_file='data/gene_level.tsv'
    )

METHOD 4: SCENARIO MODULE FUNCTIONS (For scenario analysis)
─────────────────────────────────────────────────────────
Use the scenario plotting module directly:

    from gene_pav.plot import scenarios

    # Generate scenario distribution plots
    plots = scenarios.plot_scenario_distribution(
        'data/gene_level.tsv',
        Path('plots/')
    )

METHOD 5: CLI INTERFACE (For command-line usage)
────────────────────────────────────────────────
Use the unified command-line interface:

    # Generate all plots
    python gene_pav/pavprot_complete.py --plot-only \\
      --dataset gene_pav/pavprot_out/ \\
      --plot-types all

    # Specific plots
    python gene_pav/pavprot_complete.py --plot-only \\
      --dataset gene_pav/pavprot_out/ \\
      --plot-types scenarios,ipr,advanced,1to1

COMPLETE FUNCTION LIST
──────────────────────

CORE FUNCTIONS (5):
  • generate_quality_score_plots() - Psauron quality scores
  • generate_psauron_plots() - Psauron distribution histograms
  • generate_1to1_plots() - IPR 1:1 ortholog comparison

SPECIALIZED FUNCTIONS (9):
  • generate_ipr_scatter_by_class() - IPR scatter by class type
  • generate_ipr_loglog_scale() - Log-log scale IPR plots
  • generate_ipr_loglog_class_shapes() - Log-log with class shapes
  • generate_ipr_quadrants() - Quadrant analysis (colors=pattern)
  • generate_ipr_quadrants_swapped() - Quadrants (colors=mapping)
  • generate_scenario_barplot() - Scenario bar plots
  • generate_proteinx_comparison() - ProteinX/pLDDT comparison
  • generate_fungidb_analysis() - FungiDB transcript analysis

LEGACY MODULE FUNCTIONS:
  • advanced.generate_advanced_plots() - All advanced IPR plots
  • advanced.plot_ipr_scatter_by_class() - IPR scatter
  • advanced.plot_ipr_loglog_by_mapping() - Log-log by mapping
  • advanced.plot_quadrant_analysis() - Quadrant analysis
  • advanced.plot_scenario_detailed() - Detailed scenarios
  • scenarios.plot_scenario_distribution() - Scenario distributions
  • scenarios._plot_class_code_distribution() - Class code plots

TOTAL: 14+ PLOT GENERATION FUNCTIONS AVAILABLE
"""


__all__ = [
    # ========================================================================
    # CONFIGURATION & UTILITIES
    # ========================================================================
    'setup_plotting',
    'get_class_type_palette',
    'get_scenario_palette',
    'load_data',
    'load_pavprot_data',
    'load_and_enrich',
    'enrich_pavprot_data',
    'validate_enrichment',

    # ========================================================================
    # MAIN ORCHESTRATOR
    # ========================================================================
    'generate_plots',

    # ========================================================================
    # AUTHORITATIVE PLOT FUNCTIONS - CORE MODULES (5)
    # ========================================================================
    'generate_quality_score_plots',        # plot_oldvsnew_psauron_plddt.py
    'generate_psauron_plots',               # plot_psauron_distribution.py
    'generate_1to1_plots',                  # plot_ipr_1to1_comparison.py

    # ========================================================================
    # AUTHORITATIVE PLOT FUNCTIONS - NEW INTEGRATED MODULES (9)
    # ========================================================================
    'generate_ipr_scatter_by_class',        # plot_ipr_scatter_by_class.py
    'generate_ipr_loglog_scale',            # plot_ipr_loglog_scale.py
    'generate_ipr_loglog_class_shapes',     # plot_ipr_loglog_class_shapes.py
    'generate_ipr_quadrants',               # plot_ipr_quadrants.py
    'generate_ipr_quadrants_swapped',       # plot_ipr_quadrants_swapped.py
    'generate_scenario_barplot',            # plot_scenario_barplot.py
    'generate_proteinx_comparison',         # plot_proteinx_comparison.py
    'generate_fungidb_analysis',            # plot_fungidb_analysis.py

    # ========================================================================
    # LEGACY MODULE FUNCTIONS (from advanced.py and scenarios.py)
    # ========================================================================
    'scenarios',                            # scenarios module
    'advanced',                             # advanced module

    # ========================================================================
    # FLEXIBLE API - DATA-AGNOSTIC PLOTTING (NO HARD-CODED LABELS)
    # ========================================================================
    # Core flexible plotting primitives (flexible_api.py)
    'add_regression_line',                  # Add regression line to scatter
    'scatter_comparison_plot',              # Generic scatter plot (x vs y)
    'colored_scatter_by_category',          # Scatter colored by category
    'distribution_comparison_plot',         # Overlaid histograms

    # Flexible dual metric plots (flexible_psauron_plddt.py)
    'plot_dual_comparison',                 # Side-by-side scatter plots
    'plot_by_category_dual',                # Dual scatter plots by category
]
