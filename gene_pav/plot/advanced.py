"""
Advanced plotting functions for PAVprot results.

Extracted and refactored from project_scripts/run_pipeline.py.
Provides reusable plotting functions for:
- IPR scatter plots (linear and log-log scale)
- Quadrant analysis (domain gain/loss)
- Scenario bar plots with detailed breakdowns
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


# Default configuration
DEFAULT_CONFIG = {
    'figure_dpi': 150,
    'scatter_alpha': 0.6,
    'scatter_size': 20,
}

# Mapping type shapes
MAPPING_SHAPES = {
    '1to1': 'o',      # circle
    '1to2N': '^',     # triangle up
    '1to2N+': 's',    # square
    'Nto1': 'v',      # triangle down
    'CDI': 'D',       # diamond
}

# Class type colors
CLASS_COLORS = {
    'a': '#1f77b4',      # blue (exact match)
    '=': '#1f77b4',      # blue (exact match alias)
    'ckmnj': '#2ca02c',  # green
    'ackmnj': '#ff7f0e', # orange
    'ackmnje': '#bcbd22', # olive
    'e': '#d62728',      # red
    'pru': '#9467bd',    # purple
    'sx': '#e377c2',     # pink
    'o': '#7f7f7f',      # gray
    'iy': '#17becf',     # cyan
}


def mapping_type_to_colon(mapping_type: str) -> str:
    """Convert mapping type to colon notation for display."""
    mapping = {
        '1to1': '1:1',
        '1to2N': '1:2N',
        '1to2N+': '1:2N+',
        'Nto1': 'N:1',
        'CDI': 'CDI',
    }
    return mapping.get(mapping_type, mapping_type)


def plot_ipr_scatter_by_class(
    df: pd.DataFrame,
    output_path: Path,
    x_col: str = 'ref_total_ipr_domain_length',
    y_col: str = 'query_total_ipr_domain_length',
    class_col: str = 'class_type_gene',
    config: Dict[str, Any] = None
) -> Optional[Path]:
    """
    Generate IPR domain length scatter plot colored by class type.

    Args:
        df: DataFrame with IPR length columns and class type
        output_path: Path to save the figure
        x_col: Column name for x-axis (old/ref annotation)
        y_col: Column name for y-axis (new/query annotation)
        class_col: Column name for class type coloring
        config: Optional configuration dict

    Returns:
        Path to output file, or None if failed
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for plotting")
        return None

    config = config or DEFAULT_CONFIG

    if x_col not in df.columns or y_col not in df.columns:
        logger.warning(f"Required columns not found: {x_col}, {y_col}")
        return None

    # Filter data
    cols = [x_col, y_col]
    if class_col in df.columns:
        cols.append(class_col)

    plot_df = df[cols].dropna()

    if len(plot_df) == 0:
        logger.warning("No valid data to plot")
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    if class_col in plot_df.columns:
        class_types = plot_df[class_col].unique()
        for ctype in class_types:
            mask = plot_df[class_col] == ctype
            color = CLASS_COLORS.get(ctype, '#7f7f7f')
            ax.scatter(
                plot_df.loc[mask, x_col],
                plot_df.loc[mask, y_col],
                c=color,
                label=ctype,
                alpha=config['scatter_alpha'],
                s=config['scatter_size']
            )
        ax.legend(title='Class Type', bbox_to_anchor=(1.02, 1), loc='upper left')
    else:
        ax.scatter(
            plot_df[x_col],
            plot_df[y_col],
            alpha=config['scatter_alpha'],
            s=config['scatter_size']
        )

    ax.set_xlabel('Old annotation total IPR domain length (aa)')
    ax.set_ylabel('New annotation total IPR domain length (aa)')
    ax.set_title('Gene Pair IPR Domain Length Comparison')

    # Add diagonal line
    max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label='y=x')

    plt.tight_layout()
    fig.savefig(output_path, dpi=config['figure_dpi'], bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Saved: {output_path}")
    return output_path


def plot_ipr_loglog_by_mapping(
    df: pd.DataFrame,
    output_path: Path,
    x_col: str = 'ref_total_ipr_domain_length',
    y_col: str = 'query_total_ipr_domain_length',
    mapping_col: str = 'mapping_type',
    config: Dict[str, Any] = None
) -> Optional[Path]:
    """
    Generate log-log scale IPR scatter plot with shapes by mapping type.

    Args:
        df: DataFrame with IPR length and mapping type columns
        output_path: Path to save the figure
        x_col: Column for x-axis
        y_col: Column for y-axis
        mapping_col: Column for mapping type shapes
        config: Optional configuration dict

    Returns:
        Path to output file, or None if failed
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for plotting")
        return None

    config = config or DEFAULT_CONFIG

    if x_col not in df.columns or y_col not in df.columns:
        logger.warning(f"Required columns not found: {x_col}, {y_col}")
        return None

    # Filter for positive values (log scale)
    plot_df = df[[x_col, y_col, mapping_col]].dropna()
    plot_df = plot_df[(plot_df[x_col] > 0) & (plot_df[y_col] > 0)]

    if len(plot_df) == 0:
        logger.warning("No valid data for log-log plot")
        return None

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    mapping_types = plot_df[mapping_col].unique()
    colors = plt.cm.Set1(np.linspace(0, 1, len(mapping_types)))

    for mtype, color in zip(mapping_types, colors):
        mask = plot_df[mapping_col] == mtype
        marker = MAPPING_SHAPES.get(mtype, 'o')
        label = mapping_type_to_colon(mtype)
        ax.scatter(
            plot_df.loc[mask, x_col],
            plot_df.loc[mask, y_col],
            c=[color],
            marker=marker,
            label=label,
            alpha=config['scatter_alpha'],
            s=config['scatter_size'] * 1.5
        )

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Old annotation total IPR domain length (aa) [log]')
    ax.set_ylabel('New annotation total IPR domain length (aa) [log]')
    ax.set_title('Gene Pair IPR Domain Length (Log-Log Scale)')
    ax.legend(title='Mapping Type', bbox_to_anchor=(1.02, 1), loc='upper left')

    # Add diagonal line
    min_val = max(1, min(plot_df[x_col].min(), plot_df[y_col].min()))
    max_val = max(plot_df[x_col].max(), plot_df[y_col].max())
    ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.3)

    plt.tight_layout()
    fig.savefig(output_path, dpi=config['figure_dpi'], bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Saved: {output_path}")
    return output_path


def plot_quadrant_analysis(
    df: pd.DataFrame,
    output_path: Path,
    x_col: str = 'ref_total_ipr_domain_length',
    y_col: str = 'query_total_ipr_domain_length',
    threshold: float = 0.0,
    config: Dict[str, Any] = None
) -> Optional[Path]:
    """
    Generate quadrant analysis plot showing domain gain/loss.

    Quadrants:
    - Q1 (upper-right): Both have domains (conserved)
    - Q2 (upper-left): New has domains, old doesn't (gained)
    - Q3 (lower-left): Neither has domains
    - Q4 (lower-right): Old has domains, new doesn't (lost)

    Args:
        df: DataFrame with IPR length columns
        output_path: Path to save the figure
        x_col: Column for old annotation
        y_col: Column for new annotation
        threshold: Threshold for "has domains" (default: 0)
        config: Optional configuration dict

    Returns:
        Path to output file, or None if failed
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for plotting")
        return None

    config = config or DEFAULT_CONFIG

    if x_col not in df.columns or y_col not in df.columns:
        logger.warning(f"Required columns not found: {x_col}, {y_col}")
        return None

    plot_df = df[[x_col, y_col]].dropna()

    if len(plot_df) == 0:
        logger.warning("No valid data for quadrant analysis")
        return None

    # Classify into quadrants
    def classify_quadrant(row):
        old_has = row[x_col] > threshold
        new_has = row[y_col] > threshold
        if old_has and new_has:
            return 'Conserved'
        elif not old_has and new_has:
            return 'Gained'
        elif old_has and not new_has:
            return 'Lost'
        else:
            return 'Neither'

    plot_df = plot_df.copy()
    plot_df['quadrant'] = plot_df.apply(classify_quadrant, axis=1)

    # Colors for quadrants
    quadrant_colors = {
        'Conserved': '#2ecc71',  # green
        'Gained': '#3498db',     # blue
        'Lost': '#e74c3c',       # red
        'Neither': '#95a5a6',    # gray
    }

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    for quad, color in quadrant_colors.items():
        mask = plot_df['quadrant'] == quad
        count = mask.sum()
        ax.scatter(
            plot_df.loc[mask, x_col],
            plot_df.loc[mask, y_col],
            c=color,
            label=f'{quad} (n={count:,})',
            alpha=config['scatter_alpha'],
            s=config['scatter_size']
        )

    ax.axhline(y=threshold, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(x=threshold, color='gray', linestyle='--', alpha=0.5)

    ax.set_xlabel('Old annotation total IPR domain length (aa)')
    ax.set_ylabel('New annotation total IPR domain length (aa)')
    ax.set_title('IPR Domain Quadrant Analysis (Gain/Loss)')
    ax.legend(title='Status', bbox_to_anchor=(1.02, 1), loc='upper left')

    plt.tight_layout()
    fig.savefig(output_path, dpi=config['figure_dpi'], bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Saved: {output_path}")
    return output_path


def plot_scenario_detailed(
    df: pd.DataFrame,
    output_path: Path,
    scenario_col: str = 'scenario',
    mapping_col: str = 'mapping_type',
    config: Dict[str, Any] = None
) -> Optional[Path]:
    """
    Generate detailed scenario bar plot with stacked mapping types.

    Args:
        df: DataFrame with scenario and mapping type columns
        output_path: Path to save the figure
        scenario_col: Column name for scenario
        mapping_col: Column name for mapping type
        config: Optional configuration dict

    Returns:
        Path to output file, or None if failed
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for plotting")
        return None

    config = config or DEFAULT_CONFIG

    if scenario_col not in df.columns:
        logger.warning(f"Scenario column not found: {scenario_col}")
        return None

    # Count by scenario
    scenario_counts = df[scenario_col].value_counts()

    # Define order and colors
    scenario_order = ['E', 'A', 'J', 'B', 'CDI']
    scenario_colors = {
        'E': '#2ecc71',
        'A': '#3498db',
        'J': '#9b59b6',
        'B': '#e74c3c',
        'CDI': '#f39c12',
    }

    existing = [s for s in scenario_order if s in scenario_counts.index]
    counts = [scenario_counts.get(s, 0) for s in existing]
    colors = [scenario_colors.get(s, '#95a5a6') for s in existing]

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Simple bar chart
    bars = ax1.bar(existing, counts, color=colors, edgecolor='black', linewidth=0.5)
    for bar, count in zip(bars, counts):
        ax1.annotate(f'{count:,}',
                     xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                     xytext=(0, 3), textcoords="offset points",
                     ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.set_xlabel('Scenario')
    ax1.set_ylabel('Count')
    ax1.set_title('Gene Mapping Scenarios')

    # Right: Pie chart
    ax2.pie(counts, labels=existing, colors=colors, autopct='%1.1f%%',
            startangle=90, explode=[0.02] * len(existing))
    ax2.set_title('Scenario Distribution')

    plt.tight_layout()
    fig.savefig(output_path, dpi=config['figure_dpi'], bbox_inches='tight')
    plt.close(fig)

    logger.info(f"Saved: {output_path}")
    return output_path


def generate_advanced_plots(
    output_dir: str,
    gene_level_file: str = None,
    transcript_level_file: str = None,
    config: Dict[str, Any] = None
) -> List[str]:
    """
    Generate all advanced plots from gene-level or transcript-level data.

    Args:
        output_dir: Output directory for plots
        gene_level_file: Path to gene-level TSV
        transcript_level_file: Path to transcript-level TSV
        config: Optional configuration dict

    Returns:
        List of generated plot file paths
    """
    config = config or DEFAULT_CONFIG
    plots_dir = Path(output_dir) / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    # Load gene-level data if available
    df = None
    if gene_level_file and Path(gene_level_file).exists():
        df = pd.read_csv(gene_level_file, sep='\t')
        logger.info(f"Loaded gene-level data: {len(df)} rows")
    elif transcript_level_file and Path(transcript_level_file).exists():
        df = pd.read_csv(transcript_level_file, sep='\t')
        logger.info(f"Loaded transcript-level data: {len(df)} rows")

    if df is None:
        logger.warning("No data file available for advanced plots")
        return []

    # Detect column names (handle old/new vs ref/query naming)
    x_col = None
    y_col = None
    for col in ['ref_total_ipr_domain_length', 'old_total_ipr_domain_length']:
        if col in df.columns:
            x_col = col
            break
    for col in ['query_total_ipr_domain_length', 'new_total_ipr_domain_length']:
        if col in df.columns:
            y_col = col
            break

    # Generate IPR scatter by class type
    if x_col and y_col:
        path = plot_ipr_scatter_by_class(
            df, plots_dir / 'ipr_scatter_by_class.png',
            x_col=x_col, y_col=y_col, config=config
        )
        if path:
            generated_files.append(str(path))

        # Generate log-log plot if mapping_type exists
        if 'mapping_type' in df.columns:
            path = plot_ipr_loglog_by_mapping(
                df, plots_dir / 'ipr_loglog_by_mapping.png',
                x_col=x_col, y_col=y_col, config=config
            )
            if path:
                generated_files.append(str(path))

        # Generate quadrant analysis
        path = plot_quadrant_analysis(
            df, plots_dir / 'ipr_quadrant_analysis.png',
            x_col=x_col, y_col=y_col, config=config
        )
        if path:
            generated_files.append(str(path))

    # Generate scenario plot if available
    scenario_col = None
    for col in ['scenario', 'Scenario', 'SCENARIO']:
        if col in df.columns:
            scenario_col = col
            break

    if scenario_col:
        path = plot_scenario_detailed(
            df, plots_dir / 'scenario_detailed.png',
            scenario_col=scenario_col, config=config
        )
        if path:
            generated_files.append(str(path))

    return generated_files
