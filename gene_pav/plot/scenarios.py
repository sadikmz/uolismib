"""
Scenario distribution plots for PAVprot results.

Generates bar charts showing distribution of gene mapping scenarios
(E, A, B, J, CDI) and class codes.
"""

from pathlib import Path
from typing import List
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Try to import plotting libraries
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not installed. Plotting disabled.")

try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


def plot_scenario_distribution(gene_level_file: str, plots_dir: Path) -> List[str]:
    """
    Generate scenario distribution bar chart.

    Args:
        gene_level_file: Path to gene-level TSV file
        plots_dir: Output directory for plots

    Returns:
        List of generated plot file paths
    """
    if not HAS_MATPLOTLIB:
        logger.error("matplotlib required for plotting. Install with: pip install matplotlib")
        return []

    generated_files = []

    # Load data with enrichment
    try:
        from .data_prep import load_and_enrich
        df = load_and_enrich(gene_level_file)
    except Exception as e:
        logger.warning(f"Data enrichment failed: {e}. Loading raw data instead.")
        df = pd.read_csv(gene_level_file, sep='\t')

    # Check for scenario column
    scenario_col = None
    for col in ['scenario', 'Scenario', 'SCENARIO']:
        if col in df.columns:
            scenario_col = col
            break

    if scenario_col is None:
        logger.warning("No scenario column found in gene-level file")
        return []

    # Count scenarios
    scenario_counts = df[scenario_col].value_counts()

    # Define scenario order and colors
    scenario_order = ['E', 'A', 'J', 'B', 'CDI']
    scenario_labels = {
        'E': 'E (1:1)',
        'A': 'A (1:2N)',
        'J': 'J (1:2N+)',
        'B': 'B (N:1)',
        'CDI': 'CDI (complex)'
    }
    scenario_colors = {
        'E': '#2ecc71',   # Green - stable
        'A': '#3498db',   # Blue - split
        'J': '#9b59b6',   # Purple - multi-split
        'B': '#e74c3c',   # Red - merge
        'CDI': '#f39c12'  # Orange - complex
    }

    # Filter to existing scenarios
    existing_scenarios = [s for s in scenario_order if s in scenario_counts.index]
    counts = [scenario_counts.get(s, 0) for s in existing_scenarios]
    labels = [scenario_labels.get(s, s) for s in existing_scenarios]
    colors = [scenario_colors.get(s, '#95a5a6') for s in existing_scenarios]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(labels, counts, color=colors, edgecolor='black', linewidth=0.5)

    # Add count labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.annotate(f'{count:,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_xlabel('Mapping Scenario', fontsize=12)
    ax.set_ylabel('Number of Gene Pairs', fontsize=12)
    ax.set_title('Gene Mapping Scenario Distribution', fontsize=14, fontweight='bold')

    # Add total count annotation
    total = sum(counts)
    ax.text(0.98, 0.98, f'Total: {total:,}',
            transform=ax.transAxes, ha='right', va='top',
            fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    # Save plot
    output_file = plots_dir / 'scenario_distribution.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    generated_files.append(str(output_file))
    logger.info(f"Saved: {output_file}")

    # Also generate class code distribution if available
    class_code_files = _plot_class_code_distribution(df, plots_dir)
    generated_files.extend(class_code_files)

    return generated_files


def _plot_class_code_distribution(df: pd.DataFrame, plots_dir: Path) -> List[str]:
    """
    Generate class code distribution plot.

    Args:
        df: Gene-level DataFrame
        plots_dir: Output directory

    Returns:
        List of generated file paths
    """
    generated_files = []

    # Look for class code column
    class_col = None
    for col in ['gene_pair_class_code', 'class_code', 'transcript_pair_class_code']:
        if col in df.columns:
            class_col = col
            break

    if class_col is None:
        return []

    # Explode multi-value class codes (e.g., "em,j,n")
    all_codes = []
    for codes in df[class_col].dropna():
        if isinstance(codes, str):
            all_codes.extend(codes.split(','))

    if not all_codes:
        return []

    # Normalize exact match codes: 'em', 'a', and '=' all map to '='
    normalized_codes = []
    for code in all_codes:
        if code in ['em', 'a', '=']:
            normalized_codes.append('=')
        else:
            normalized_codes.append(code)

    code_counts = pd.Series(normalized_codes).value_counts()

    # GFFcompare class code definitions
    code_definitions = {
        '=': 'Exact match (reference/query exon)',
        'e': 'Single exon transcript match',
        'j': 'Junction overlap (partial)',
        'o': 'Other/overlap',
        'c': 'Contained',
        'k': 'Contains',
        'm': 'Exon overlap (main type)',
        'n': 'Novel isoform',
        'x': 'Exonic overlap',
        's': 'Strand conflict',
        'r': 'Repeat region',
        'u': 'Unknown',
        'p': 'Possible polymerase chain',
        'y': 'Polymerase slippage',
        'i': 'Intronic',
    }

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6.5))

    if HAS_SEABORN:
        colors = sns.color_palette("husl", len(code_counts))
    else:
        colors = plt.cm.tab20(range(len(code_counts)))

    bars = ax.bar(code_counts.index, code_counts.values, color=colors, edgecolor='black', linewidth=0.5)

    # Add count labels
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{int(height):,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('GFFcompare Class Code', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('GFFcompare Class Code Distribution', fontsize=14, fontweight='bold')
    plt.xticks(rotation=45, ha='right')

    # Add legend box with code definitions (only show present codes)
    legend_text = "GFFcompare Codes:\n"
    for code in sorted(code_counts.index):
        definition = code_definitions.get(code, 'Unknown')
        legend_text += f"  {code}: {definition}\n"

    ax.text(0.98, 0.97, legend_text, transform=ax.transAxes,
            fontsize=8, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()

    output_file = plots_dir / 'class_code_distribution.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    generated_files.append(str(output_file))
    logger.info(f"Saved: {output_file}")

    return generated_files
