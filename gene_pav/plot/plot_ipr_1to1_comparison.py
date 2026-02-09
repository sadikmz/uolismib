#!/usr/bin/env python3
"""
IPR Domain Length Comparison Plots for 1:1 (Scenario E) Gene Pairs

Generates scatter plots comparing IPR domain length between
Old annotation (FungiDB v68) and New annotation (NCBI RefSeq)
for 1:1 orthologous gene pairs.

Outputs:
1. ipr_1to1_all_by_class_type.png - All E pairs, colored by class type
2. ipr_1to1_all_no_class.png - All E pairs, single color
3. ipr_1to1_emckmnje1_by_class_type.png - Filtered E pairs, colored by class type
4. ipr_1to1_emckmnje1_no_class.png - Filtered E pairs, single color
5-8. Log-scale versions of the above (_log suffix)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from pathlib import Path
from typing import List, Optional

# Configuration
GENE_LEVEL_ALL = Path("output/figures_out/120126_all_out/gene_level_with_psauron.tsv")
GENE_LEVEL_FILTERED = Path("output/120126_out/gene_level_emckmnje1.tsv")
OUTPUT_DIR = Path("output/figures_out/120126_all_out")
FIGURE_DPI = 300

# Class type colors
CLASS_COLORS = {
    'a': '#1f77b4',      # blue
    'ckmnj': '#2ca02c',  # green
    'ackmnj': '#ff7f0e', # orange
    'e': '#d62728',      # red
    'pru': '#9467bd',    # purple
    'sx': '#e377c2',     # pink
    'o': '#7f7f7f',      # gray
    'ackmnje': '#bcbd22', # olive
    'iy': '#17becf',     # cyan
}


def plot_ipr_comparison(df: pd.DataFrame, output_path: Path, title: str,
                        color_by_class: bool = True, log_scale: bool = False):
    """
    Generate IPR domain length comparison scatter plot.

    Args:
        df: DataFrame with old_total_ipr_domain_length and new_total_ipr_domain_length
        output_path: Path to save the figure
        title: Plot title
        color_by_class: If True, color points by class_type_gene
        log_scale: If True, use log-log scale
    """
    # Column names (support both old/new and ref/query naming)
    ref_col = 'new_total_ipr_domain_length' if 'new_total_ipr_domain_length' in df.columns else 'ref_total_ipr_domain_length'
    qry_col = 'old_total_ipr_domain_length' if 'old_total_ipr_domain_length' in df.columns else 'query_total_ipr_domain_length'

    # Filter to rows with valid IPR data
    if ref_col not in df.columns or qry_col not in df.columns:
        print(f"  [ERROR] IPR columns not found")
        return None

    valid = df.dropna(subset=[ref_col, qry_col])
    valid = valid[(valid[ref_col] >= 0) & (valid[qry_col] >= 0)]

    if len(valid) == 0:
        print(f"  [ERROR] No valid IPR data")
        return None

    print(f"    Plotting {len(valid):,} gene pairs with IPR data")

    # Calculate correlation
    corr = valid[ref_col].corr(valid[qry_col])
    r_squared = corr ** 2

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 8))

    if color_by_class and 'class_type_gene' in valid.columns:
        # Plot by class type
        class_types = valid['class_type_gene'].unique()
        for ct in sorted(class_types):
            subset = valid[valid['class_type_gene'] == ct]
            color = CLASS_COLORS.get(ct, '#7f7f7f')
            ax.scatter(subset[ref_col], subset[qry_col],
                      alpha=0.5, s=20, c=color,
                      label=f'{ct} (n={len(subset):,})')
    else:
        # Single color
        ax.scatter(valid[ref_col], valid[qry_col],
                  alpha=0.5, s=20, c='steelblue')

    # Get axis range
    max_val = max(valid[ref_col].max(), valid[qry_col].max())
    min_val = max(1, min(valid[valid[ref_col] > 0][ref_col].min(),
                         valid[valid[qry_col] > 0][qry_col].min()))

    if log_scale:
        # Set log scale
        ax.set_xscale('log')
        ax.set_yscale('log')

        # Add y=x line for log scale
        line_range = np.logspace(np.log10(min_val), np.log10(max_val), 100)
        ax.plot(line_range, line_range, 'k--', alpha=0.5, label='y=x (perfect match)')

        # Add regression line in log space
        valid_pos = valid[(valid[ref_col] > 0) & (valid[qry_col] > 0)]
        log_ref = np.log10(valid_pos[ref_col])
        log_qry = np.log10(valid_pos[qry_col])
        slope, intercept, r_value, p_value, std_err = stats.linregress(log_ref, log_qry)
        x_line = np.logspace(np.log10(min_val), np.log10(max_val), 100)
        y_line = 10 ** (slope * np.log10(x_line) + intercept)
        ax.plot(x_line, y_line, 'r-', alpha=0.7, linewidth=2,
                label=f'Log regression (slope={slope:.2f})')

        # Set axis limits for log scale
        ax.set_xlim(min_val * 0.8, max_val * 1.2)
        ax.set_ylim(min_val * 0.8, max_val * 1.2)
        scale_label = " (log scale)"
    else:
        # Add y=x line
        ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, label='y=x (perfect match)')

        # Add regression line
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            valid[ref_col], valid[qry_col]
        )
        x_line = np.array([0, max_val])
        y_line = slope * x_line + intercept
        ax.plot(x_line, y_line, 'r-', alpha=0.7, linewidth=2,
                label=f'Regression (y={slope:.2f}x+{intercept:.0f})')

        # Set axis limits
        ax.set_xlim(0, max_val * 1.05)
        ax.set_ylim(0, max_val * 1.05)
        scale_label = ""

    # Labels and title
    ax.set_xlabel(f'New annotation total IPR domain length (aa){scale_label}', fontsize=11)
    ax.set_ylabel(f'Old annotation total IPR domain length (aa){scale_label}', fontsize=11)
    ax.set_title(f'{title}\n(Pearson r = {corr:.3f}, R² = {r_squared:.3f}, n = {len(valid):,})',
                fontsize=12)

    # Legend
    ax.legend(loc='upper left', fontsize=9)

    # Add GFFcompare class code reference if showing by class type
    if color_by_class and 'class_type_gene' in valid.columns:
        class_code_info = (
            "GFFcompare Class Types:\n"
            "  exact (a/=): Exact exon structure match\n"
            "  split (j/c): Intron overlap/contained\n"
            "  novel (n/k): Novel isoform/not in ref"
        )
        ax.text(0.98, 0.05, class_code_info, transform=ax.transAxes,
                fontsize=8, verticalalignment='bottom', horizontalalignment='left',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.7))

    plt.tight_layout()
    fig.savefig(output_path, dpi=FIGURE_DPI, bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")

    return {
        'n': len(valid),
        'r': corr,
        'r_squared': r_squared
    }


def main():
    """Generate IPR comparison plots for 1:1 gene pairs."""
    print("=" * 60)
    print("IPR Domain Comparison for 1:1 (Scenario E) Gene Pairs")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = {}

    # ===== 1. All Data - Scenario E =====
    print("\n[1/8] All Data - 1:1 Pairs with Class Type")
    print("-" * 40)

    if GENE_LEVEL_ALL.exists():
        print(f"  Loading: {GENE_LEVEL_ALL}")
        df_all = pd.read_csv(GENE_LEVEL_ALL, sep='\t')
        print(f"    Total gene pairs: {len(df_all):,}")

        # Filter to scenario E (1:1)
        df_e_all = df_all[df_all['scenario'] == 'E'].copy()
        print(f"    Scenario E (1:1) pairs: {len(df_e_all):,}")

        if len(df_e_all) > 0:
            # With class type
            results['all_class'] = plot_ipr_comparison(
                df_e_all,
                OUTPUT_DIR / "ipr_1to1_all_by_class_type.png",
                "1:1 gene mapping IPR Domain Comparison (All Data)",
                color_by_class=True
            )

            # Without class type
            print("\n[2/8] All Data - 1:1 Pairs without Class Type")
            print("-" * 40)
            results['all_no_class'] = plot_ipr_comparison(
                df_e_all,
                OUTPUT_DIR / "ipr_1to1_all_no_class.png",
                "1:1 gene mapping IPR Domain Comparison (All Data)",
                color_by_class=False
            )

            # Log scale versions
            print("\n[3/8] All Data - 1:1 Pairs with Class Type (Log Scale)")
            print("-" * 40)
            results['all_class_log'] = plot_ipr_comparison(
                df_e_all,
                OUTPUT_DIR / "ipr_1to1_all_by_class_type_log.png",
                "1:1 gene mapping IPR Domain Comparison (All Data)",
                color_by_class=True,
                log_scale=True
            )

            print("\n[4/8] All Data - 1:1 Pairs without Class Type (Log Scale)")
            print("-" * 40)
            results['all_no_class_log'] = plot_ipr_comparison(
                df_e_all,
                OUTPUT_DIR / "ipr_1to1_all_no_class_log.png",
                "1:1 gene mapping IPR Domain Comparison (All Data)",
                color_by_class=False,
                log_scale=True
            )
    else:
        print(f"  [ERROR] File not found: {GENE_LEVEL_ALL}")

    # ===== 2. Filtered Data (emckmnje=1) - Scenario E =====
    print("\n[5/8] Filtered Data (emckmnje=1) - 1:1 Pairs with Class Type")
    print("-" * 40)

    if GENE_LEVEL_FILTERED.exists():
        print(f"  Loading: {GENE_LEVEL_FILTERED}")
        df_filtered = pd.read_csv(GENE_LEVEL_FILTERED, sep='\t')
        print(f"    Total gene pairs: {len(df_filtered):,}")

        # Filter to scenario E (1:1)
        df_e_filtered = df_filtered[df_filtered['scenario'] == 'E'].copy()
        print(f"    Scenario E (1:1) pairs: {len(df_e_filtered):,}")

        if len(df_e_filtered) > 0:
            # With class type
            results['filtered_class'] = plot_ipr_comparison(
                df_e_filtered,
                OUTPUT_DIR / "ipr_1to1_emckmnje1_by_class_type.png",
                "1:1 gene mapping IPR Domain Comparison (emckmnje=1 Filtered)",
                color_by_class=True
            )

            # Without class type
            print("\n[6/8] Filtered Data (emckmnje=1) - 1:1 Pairs without Class Type")
            print("-" * 40)
            results['filtered_no_class'] = plot_ipr_comparison(
                df_e_filtered,
                OUTPUT_DIR / "ipr_1to1_emckmnje1_no_class.png",
                "1:1 gene mapping IPR Domain Comparison (emckmnje=1 Filtered)",
                color_by_class=False
            )

            # Log scale versions
            print("\n[7/8] Filtered Data (emckmnje=1) - 1:1 Pairs with Class Type (Log Scale)")
            print("-" * 40)
            results['filtered_class_log'] = plot_ipr_comparison(
                df_e_filtered,
                OUTPUT_DIR / "ipr_1to1_emckmnje1_by_class_type_log.png",
                "1:1 gene mapping IPR Domain Comparison (emckmnje=1 Filtered)",
                color_by_class=True,
                log_scale=True
            )

            print("\n[8/8] Filtered Data (emckmnje=1) - 1:1 Pairs without Class Type (Log Scale)")
            print("-" * 40)
            results['filtered_no_class_log'] = plot_ipr_comparison(
                df_e_filtered,
                OUTPUT_DIR / "ipr_1to1_emckmnje1_no_class_log.png",
                "1:1 gene mapping IPR Domain Comparison (emckmnje=1 Filtered)",
                color_by_class=False,
                log_scale=True
            )
    else:
        print(f"  [ERROR] File not found: {GENE_LEVEL_FILTERED}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for key, stats in results.items():
        if stats:
            print(f"  {key}: n={stats['n']:,}, r={stats['r']:.3f}, R²={stats['r_squared']:.3f}")

    print("\nIPR 1:1 Comparison Plots Complete!")
    print("=" * 60)


def generate_1to1_plots(
    gene_level_file: str,
    output_dir: Path,
    config: dict = None
) -> List[Path]:
    """
    Generate 1:1 IPR comparison plots for CLI integration.

    Args:
        gene_level_file: Path to gene-level TSV with scenario and IPR columns
        output_dir: Directory to save plots
        config: Optional configuration (figure_dpi, etc.)

    Returns:
        List of generated plot file paths
    """
    generated_files = []
    config = config or {'figure_dpi': FIGURE_DPI}

    if not Path(gene_level_file).exists():
        print(f"  [ERROR] File not found: {gene_level_file}")
        return generated_files

    print(f"  Loading: {gene_level_file}")
    df = pd.read_csv(gene_level_file, sep='\t')
    print(f"    Total gene pairs: {len(df):,}")

    # Filter to scenario E (1:1)
    df_e = df[df['scenario'] == 'E'].copy()
    print(f"    Scenario E (1:1) pairs: {len(df_e):,}")

    if len(df_e) == 0:
        print("  [WARN] No 1:1 gene pairs found")
        return generated_files

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate 4 variants: with/without class, linear/log
    variants = [
        ('ipr_1to1_by_class_type.png', True, False),
        ('ipr_1to1_no_class.png', False, False),
        ('ipr_1to1_by_class_type_log.png', True, True),
        ('ipr_1to1_no_class_log.png', False, True),
    ]

    for filename, color_by_class, log_scale in variants:
        result = plot_ipr_comparison(
            df_e,
            output_dir / filename,
            "1:1 gene mapping IPR Domain Comparison",
            color_by_class=color_by_class,
            log_scale=log_scale
        )
        if result:
            generated_files.append(output_dir / filename)

    return generated_files


if __name__ == "__main__":
    main()
