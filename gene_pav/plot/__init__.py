"""
Plotting modules for PAVprot output visualization.

This package provides visualization tools for analyzing PAVprot pipeline output,
including scatter plots, distribution plots, and comparative visualizations.

CLI Plot Types (via --plot argument):
    - scenarios: Scenario distribution plots (E/A/B/J/CDI)
    - bbh: BBH and pairwise alignment scatter plots
    - ipr: IPR domain length comparison plots
    - advanced: Log-log scale, quadrant analysis, detailed scenarios
    - 1to1: IPR comparison for 1:1 ortholog pairs (Scenario E)
    - psauron: Psauron score distribution histograms
    - quality: Quality score scatter plots (new vs old annotation)

Modules:
    - config: Plot configuration and styling
    - utils: Shared utility functions for data loading
    - scenarios: Scenario distribution plots
    - alignments: BBH and pairwise alignment plots
    - domains: IPR domain length comparison plots
    - advanced: Advanced plots (log-log, quadrant analysis)
    - plot_ipr_1to1_comparison: IPR 1:1 comparison for Scenario E pairs
    - plot_psauron_distribution: Psauron score distribution comparison
    - plot_oldvsnew_psauron_plddt: Old vs New quality score scatter plots
"""

from pathlib import Path
from typing import Optional, List
import logging

from .config import setup_plotting, get_class_type_palette, get_scenario_palette
from .utils import load_data, load_pavprot_data

logger = logging.getLogger(__name__)


def generate_plots(
    output_dir: str,
    plot_types: Optional[List[str]] = None,
    transcript_level_file: Optional[str] = None,
    gene_level_file: Optional[str] = None,
    bbh_file: Optional[str] = None,
    old_ipr_file: Optional[str] = None,
    new_ipr_file: Optional[str] = None,
) -> List[str]:
    """
    Generate visualization plots for PAVprot results.

    Args:
        output_dir: Main output directory (plots saved to {output_dir}/plots)
        plot_types: List of plot types to generate.
                   Options: 'scenarios', 'bbh', 'ipr', 'advanced', '1to1', 'psauron', 'quality', 'all'
                   If None or empty, generates all available plots.
        transcript_level_file: Path to transcript-level TSV output
        gene_level_file: Path to gene-level TSV output
        bbh_file: Path to BBH results TSV
        old_ipr_file: Path to old annotation IPR domain distribution TSV
        new_ipr_file: Path to new annotation IPR domain distribution TSV

    Returns:
        List of generated plot file paths
    """
    from . import scenarios, alignments, domains, advanced
    from .plot_ipr_1to1_comparison import generate_1to1_plots
    from .plot_psauron_distribution import generate_psauron_plots
    from .plot_oldvsnew_psauron_plddt import generate_quality_score_plots

    # Create plots directory
    plots_dir = Path(output_dir) / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Default to all plot types if none specified
    if not plot_types:
        plot_types = ['scenarios', 'bbh', 'ipr', 'advanced', '1to1', 'psauron', 'quality']

    # Generate scenario plots
    if 'scenarios' in plot_types:
        if gene_level_file and Path(gene_level_file).exists():
            try:
                files = scenarios.plot_scenario_distribution(gene_level_file, plots_dir)
                generated_files.extend(files)
                logger.info(f"Generated scenario plots: {len(files)} files")
            except Exception as e:
                logger.warning(f"Failed to generate scenario plots: {e}")
        else:
            logger.warning("Skipping scenario plots: gene-level file not found")

    # Generate BBH plots
    if 'bbh' in plot_types:
        if bbh_file and Path(bbh_file).exists():
            try:
                files = alignments.plot_bbh_scatter(bbh_file, plots_dir)
                generated_files.extend(files)
                logger.info(f"Generated BBH plots: {len(files)} files")
            except Exception as e:
                logger.warning(f"Failed to generate BBH plots: {e}")
        elif transcript_level_file and Path(transcript_level_file).exists():
            try:
                files = alignments.plot_alignment_metrics(transcript_level_file, plots_dir)
                generated_files.extend(files)
                logger.info(f"Generated alignment plots: {len(files)} files")
            except Exception as e:
                logger.warning(f"Failed to generate alignment plots: {e}")
        else:
            logger.warning("Skipping BBH plots: no alignment data found")

    # Generate IPR plots
    if 'ipr' in plot_types:
        if old_ipr_file or new_ipr_file:
            try:
                files = domains.plot_ipr_comparison(
                    old_ipr_file, new_ipr_file, plots_dir
                )
                generated_files.extend(files)
                logger.info(f"Generated IPR plots: {len(files)} files")
            except Exception as e:
                logger.warning(f"Failed to generate IPR plots: {e}")
        else:
            logger.warning("Skipping IPR plots: no domain data found")

    # Generate advanced plots (log-log, quadrant analysis, etc.)
    if 'advanced' in plot_types:
        try:
            files = advanced.generate_advanced_plots(
                output_dir=output_dir,
                gene_level_file=gene_level_file,
                transcript_level_file=transcript_level_file,
            )
            generated_files.extend(files)
            logger.info(f"Generated advanced plots: {len(files)} files")
        except Exception as e:
            logger.warning(f"Failed to generate advanced plots: {e}")

    # Generate 1:1 ortholog IPR comparison plots
    if '1to1' in plot_types:
        if gene_level_file and Path(gene_level_file).exists():
            try:
                files = generate_1to1_plots(gene_level_file, plots_dir)
                generated_files.extend([str(f) for f in files])
                logger.info(f"Generated 1:1 IPR plots: {len(files)} files")
            except Exception as e:
                logger.warning(f"Failed to generate 1:1 plots: {e}")
        else:
            logger.warning("Skipping 1:1 plots: gene-level file not found")

    # Generate Psauron distribution plots
    if 'psauron' in plot_types:
        if gene_level_file and Path(gene_level_file).exists():
            try:
                files = generate_psauron_plots(gene_level_file, plots_dir)
                generated_files.extend([str(f) for f in files])
                logger.info(f"Generated Psauron distribution plots: {len(files)} files")
            except Exception as e:
                logger.warning(f"Failed to generate Psauron plots: {e}")
        else:
            logger.warning("Skipping Psauron plots: gene-level file not found")

    # Generate quality score scatter plots (Psauron new vs old)
    if 'quality' in plot_types:
        if gene_level_file and Path(gene_level_file).exists():
            try:
                files = generate_quality_score_plots(gene_level_file, plots_dir)
                generated_files.extend([str(f) for f in files])
                logger.info(f"Generated quality score plots: {len(files)} files")
            except Exception as e:
                logger.warning(f"Failed to generate quality plots: {e}")
        else:
            logger.warning("Skipping quality plots: gene-level file not found")

    return generated_files


__all__ = [
    'setup_plotting',
    'get_class_type_palette',
    'get_scenario_palette',
    'load_data',
    'load_pavprot_data',
    'generate_plots',
]
