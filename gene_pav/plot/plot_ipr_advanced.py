#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
import sys
from pathlib import Path
try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("Warning: scipy not available, some plots will be skipped", file=sys.stderr)

from matplotlib.gridspec import GridSpec

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

def load_data(input_file):
    """Load PAVprot output TSV file"""
    df = pd.read_csv(input_file, sep='\t')
    return df

def plot_log_scale(df, output_prefix):
    """Log-log scale plot for wide-range data"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # Log-log scatter colored by class_code
    class_codes = df_both['class_code'].unique()
    colors = sns.color_palette("husl", len(class_codes))
    color_map = dict(zip(class_codes, colors))

    for code in sorted(class_codes):
        subset = df_both[df_both['class_code'] == code]
        ax1.scatter(subset['query_total_ipr_domain_length'],
                   subset['ref_total_ipr_domain_length'],
                   c=[color_map[code]], label=f'{code}',
                   alpha=0.6, s=35, edgecolors='black', linewidth=0.2)

    # Diagonal line
    min_val = min(df_both['query_total_ipr_domain_length'].min(),
                  df_both['ref_total_ipr_domain_length'].min())
    max_val = max(df_both['query_total_ipr_domain_length'].max(),
                  df_both['ref_total_ipr_domain_length'].max())
    ax1.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, linewidth=2)

    ax1.set_xscale('log')
    ax1.set_yscale('log')
    ax1.set_xlabel('Query Total IPR Domain Length (aa, log scale)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Reference Total IPR Domain Length (aa, log scale)', fontsize=12, fontweight='bold')
    ax1.set_title('Log-Log Scale Plot by Class Code', fontsize=14, fontweight='bold')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    ax1.grid(True, alpha=0.3, which='both')

    # Hexbin log scale
    hexbin = ax2.hexbin(df_both['query_total_ipr_domain_length'],
                        df_both['ref_total_ipr_domain_length'],
                        xscale='log', yscale='log',
                        gridsize=40, cmap='YlOrRd', mincnt=1)
    ax2.plot([min_val, max_val], [min_val, max_val], 'b--', alpha=0.7, linewidth=2)
    ax2.set_xlabel('Query Total IPR Domain Length (aa, log scale)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Reference Total IPR Domain Length (aa, log scale)', fontsize=12, fontweight='bold')
    ax2.set_title('Log-Log Density Plot', fontsize=14, fontweight='bold')
    cb = plt.colorbar(hexbin, ax=ax2)
    cb.set_label('Count', fontsize=10, fontweight='bold')
    ax2.grid(True, alpha=0.3, which='both')

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_loglog_scale.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_loglog_scale.png", file=sys.stderr)
    plt.close()

def plot_regression_analysis(df, output_prefix):
    """Regression analysis with residuals"""

    if not HAS_SCIPY:
        print("Skipping regression analysis (requires scipy)", file=sys.stderr)
        return

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

    # Regression with confidence interval
    ax1 = fig.add_subplot(gs[0, :])

    # Calculate regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df_both['ref_total_ipr_domain_length'],
        df_both['query_total_ipr_domain_length'])

    x = df_both['ref_total_ipr_domain_length']
    y = df_both['query_total_ipr_domain_length']

    # Scatter
    ax1.scatter(x, y, alpha=0.3, s=20, c='steelblue', edgecolors='none')

    # Regression line
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept
    ax1.plot(x_line, y_line, 'r-', linewidth=2,
             label=f'y = {slope:.2f}x + {intercept:.1f}\nR² = {r_value**2:.4f}')

    # Identity line
    max_val = max(x.max(), y.max())
    ax1.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2, label='y = x')

    ax1.set_xlabel('Reference Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Query Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax1.set_title('Linear Regression Analysis', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Calculate residuals
    predicted = slope * x + intercept
    residuals = y - predicted
    df_both['residuals'] = residuals
    df_both['predicted'] = predicted

    # Residual plot
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.scatter(df_both['predicted'], df_both['residuals'],
                alpha=0.3, s=20, c='steelblue', edgecolors='none')
    ax2.axhline(0, color='red', linestyle='--', linewidth=2)
    ax2.set_xlabel('Predicted Query Length (aa)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Residuals (aa)', fontsize=11, fontweight='bold')
    ax2.set_title('Residual Plot', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    # Q-Q plot for residuals
    ax3 = fig.add_subplot(gs[1, 1])
    stats.probplot(residuals, dist="norm", plot=ax3)
    ax3.set_title('Q-Q Plot of Residuals', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)

    plt.savefig(f"{output_prefix}_regression_analysis.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_regression_analysis.png", file=sys.stderr)
    plt.close()

def plot_faceted_by_emckmnj(df, output_prefix):
    """Faceted plots by emckmnj flag"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    for idx, emckmnj_val in enumerate([0, 1]):
        subset = df_both[df_both['emckmnj'] == emckmnj_val]
        ax = axes[idx]

        if len(subset) == 0:
            continue

        # Hexbin
        hexbin = ax.hexbin(subset['query_total_ipr_domain_length'],
                          subset['ref_total_ipr_domain_length'],
                          gridsize=40, cmap='YlOrRd', mincnt=1)

        max_val = max(subset['query_total_ipr_domain_length'].max(),
                      subset['ref_total_ipr_domain_length'].max())
        ax.plot([0, max_val], [0, max_val], 'b--', alpha=0.7, linewidth=2)

        corr = subset['query_total_ipr_domain_length'].corr(
            subset['ref_total_ipr_domain_length'])

        title = 'emckmnj = 1 (em,c,k,m,n,j)' if emckmnj_val == 1 else 'emckmnj = 0 (other)'
        ax.set_xlabel('Query Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Reference Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
        ax.set_title(f'{title}\nn={len(subset)}, r={corr:.3f}', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)

        cb = plt.colorbar(hexbin, ax=ax)
        cb.set_label('Count', fontsize=10)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_by_emckmnj.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_by_emckmnj.png", file=sys.stderr)
    plt.close()


def plot_bland_altman(df, output_prefix):
    """Bland-Altman plot for method agreement analysis"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    query = df_both['query_total_ipr_domain_length']
    ref = df_both['ref_total_ipr_domain_length']

    mean_vals = (query + ref) / 2
    diff_vals = query - ref

    mean_diff = diff_vals.mean()
    std_diff = diff_vals.std()

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.scatter(mean_vals, diff_vals, alpha=0.3, s=20, c='steelblue', edgecolors='none')

    # Mean line
    ax.axhline(mean_diff, color='red', linestyle='-', linewidth=2,
               label=f'Mean: {mean_diff:.1f}')

    # Limits of agreement (mean ± 1.96*SD)
    upper_loa = mean_diff + 1.96 * std_diff
    lower_loa = mean_diff - 1.96 * std_diff
    ax.axhline(upper_loa, color='gray', linestyle='--', linewidth=1.5,
               label=f'+1.96 SD: {upper_loa:.1f}')
    ax.axhline(lower_loa, color='gray', linestyle='--', linewidth=1.5,
               label=f'-1.96 SD: {lower_loa:.1f}')

    ax.set_xlabel('Mean of Query and Reference (aa)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Difference (Query - Reference) (aa)', fontsize=12, fontweight='bold')
    ax.set_title('Bland-Altman Plot', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_bland_altman.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_bland_altman.png", file=sys.stderr)
    plt.close()


def plot_delta_distribution(df, output_prefix):
    """Distribution of differences between query and reference"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    delta = df_both['query_total_ipr_domain_length'] - df_both['ref_total_ipr_domain_length']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Histogram
    ax1.hist(delta, bins=50, color='steelblue', edgecolor='black', alpha=0.7)
    ax1.axvline(0, color='red', linestyle='--', linewidth=2, label='Zero difference')
    ax1.axvline(delta.mean(), color='orange', linestyle='-', linewidth=2,
                label=f'Mean: {delta.mean():.1f}')
    ax1.set_xlabel('Difference (Query - Reference) (aa)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax1.set_title('Distribution of IPR Domain Length Differences', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Box plot by class_code
    class_codes = sorted(df_both['class_code'].unique())
    data_by_class = [df_both[df_both['class_code'] == cc]['query_total_ipr_domain_length'] -
                     df_both[df_both['class_code'] == cc]['ref_total_ipr_domain_length']
                     for cc in class_codes]

    bp = ax2.boxplot(data_by_class, labels=class_codes, patch_artist=True)
    colors = sns.color_palette("husl", len(class_codes))
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    ax2.axhline(0, color='red', linestyle='--', linewidth=1.5)
    ax2.set_xlabel('Class Code', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Difference (Query - Reference) (aa)', fontsize=12, fontweight='bold')
    ax2.set_title('Differences by Class Code', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_delta_distribution.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_delta_distribution.png", file=sys.stderr)
    plt.close()


def plot_violin_comparison(df, output_prefix):
    """Violin plot comparing query and reference distributions"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    # Reshape for plotting
    plot_data = pd.DataFrame({
        'Length': pd.concat([df_both['query_total_ipr_domain_length'],
                            df_both['ref_total_ipr_domain_length']]),
        'Type': ['Query'] * len(df_both) + ['Reference'] * len(df_both),
        'Class Code': pd.concat([df_both['class_code'], df_both['class_code']])
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Overall violin
    sns.violinplot(data=plot_data, x='Type', y='Length', ax=ax1,
                   palette=['steelblue', 'coral'], inner='box')
    ax1.set_xlabel('', fontsize=12)
    ax1.set_ylabel('Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax1.set_title('Query vs Reference Distribution', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # By class code
    class_codes = sorted(df_both['class_code'].unique())
    if len(class_codes) <= 8:
        sns.violinplot(data=plot_data, x='Class Code', y='Length', hue='Type',
                       ax=ax2, palette=['steelblue', 'coral'], split=True, inner='quart')
        ax2.set_xlabel('Class Code', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
        ax2.set_title('Distribution by Class Code', fontsize=13, fontweight='bold')
        ax2.legend(title='Type', fontsize=9)
        ax2.grid(True, alpha=0.3, axis='y')
    else:
        ax2.text(0.5, 0.5, f'Too many class codes ({len(class_codes)})\nfor violin plot',
                 ha='center', va='center', fontsize=12, transform=ax2.transAxes)
        ax2.set_title('Distribution by Class Code', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_violin_comparison.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_violin_comparison.png", file=sys.stderr)
    plt.close()


def plot_cdf_comparison(df, output_prefix):
    """Cumulative distribution function comparison"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    fig, ax = plt.subplots(figsize=(10, 7))

    # Sort values for CDF
    query_sorted = np.sort(df_both['query_total_ipr_domain_length'])
    ref_sorted = np.sort(df_both['ref_total_ipr_domain_length'])

    # CDF values
    cdf = np.arange(1, len(query_sorted) + 1) / len(query_sorted)

    ax.plot(query_sorted, cdf, 'b-', linewidth=2, label='Query')
    ax.plot(ref_sorted, cdf, 'r-', linewidth=2, label='Reference')

    ax.set_xlabel('Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Cumulative Probability', fontsize=12, fontweight='bold')
    ax.set_title('CDF Comparison: Query vs Reference', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Add KS test if scipy available
    if HAS_SCIPY:
        ks_stat, p_value = stats.ks_2samp(query_sorted, ref_sorted)
        ax.text(0.95, 0.05, f'KS statistic: {ks_stat:.4f}\np-value: {p_value:.2e}',
                transform=ax.transAxes, ha='right', va='bottom',
                fontsize=10, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_cdf_comparison.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_cdf_comparison.png", file=sys.stderr)
    plt.close()


def plot_contour_density(df, output_prefix):
    """Contour density plot for query vs reference"""

    if not HAS_SCIPY:
        print("Skipping contour density plot (requires scipy)", file=sys.stderr)
        return

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) < 10:
        return

    fig, ax = plt.subplots(figsize=(10, 8))

    x = df_both['query_total_ipr_domain_length']
    y = df_both['ref_total_ipr_domain_length']

    # Create 2D histogram for contours
    try:
        # KDE for smooth contours
        from scipy.stats import gaussian_kde
        xy = np.vstack([x, y])
        kde = gaussian_kde(xy)

        # Grid for evaluation
        xmin, xmax = x.min(), x.max()
        ymin, ymax = y.min(), y.max()
        xx, yy = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
        positions = np.vstack([xx.ravel(), yy.ravel()])
        zz = np.reshape(kde(positions).T, xx.shape)

        # Contour plot
        contour = ax.contourf(xx, yy, zz, levels=20, cmap='YlOrRd')
        plt.colorbar(contour, ax=ax, label='Density')

        # Scatter overlay
        ax.scatter(x, y, alpha=0.2, s=10, c='black', edgecolors='none')

    except Exception as e:
        # Fallback to hexbin
        print(f"KDE failed, using hexbin: {e}", file=sys.stderr)
        hexbin = ax.hexbin(x, y, gridsize=40, cmap='YlOrRd', mincnt=1)
        plt.colorbar(hexbin, ax=ax, label='Count')

    # Diagonal
    max_val = max(x.max(), y.max())
    ax.plot([0, max_val], [0, max_val], 'b--', alpha=0.7, linewidth=2)

    ax.set_xlabel('Query Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Reference Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax.set_title('Density Contour Plot', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_contour_density.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_contour_density.png", file=sys.stderr)
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Advanced plots for query vs reference total IPR domain lengths"
    )
    parser.add_argument('input', help="PAVprot output TSV file")
    parser.add_argument('--output-prefix', '-o', default='ipr_advanced',
                       help="Output prefix for plot files")

    args = parser.parse_args()

    print(f"\nLoading data from: {args.input}", file=sys.stderr)
    df = load_data(args.input)
    print(f"Loaded {len(df)} entries", file=sys.stderr)

    # Create output directory
    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\nGenerating advanced plots...", file=sys.stderr)
    plot_bland_altman(df, args.output_prefix)
    plot_log_scale(df, args.output_prefix)
    plot_delta_distribution(df, args.output_prefix)
    plot_violin_comparison(df, args.output_prefix)
    plot_cdf_comparison(df, args.output_prefix)
    plot_regression_analysis(df, args.output_prefix)
    plot_faceted_by_emckmnj(df, args.output_prefix)
    plot_contour_density(df, args.output_prefix)

    print("\n✓ All advanced plots generated successfully!", file=sys.stderr)

if __name__ == '__main__':
    main()
