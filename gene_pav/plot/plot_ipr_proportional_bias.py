#!/usr/bin/env python3
"""
Analyze proportional bias and identify class codes with most disagreement
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
import sys
from pathlib import Path
from matplotlib.gridspec import GridSpec

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

def load_data(input_file):
    """Load PAVprot output TSV file"""
    df = pd.read_csv(input_file, sep='\t')
    return df

def plot_proportional_bias_analysis(df, output_prefix):
    """Detailed analysis of proportional bias"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    # Calculate Bland-Altman metrics
    df_both['mean'] = (df_both['query_total_ipr_domain_length'] +
                       df_both['ref_total_ipr_domain_length']) / 2
    df_both['diff'] = (df_both['query_total_ipr_domain_length'] -
                       df_both['ref_total_ipr_domain_length'])
    df_both['abs_diff'] = df_both['diff'].abs()
    df_both['ratio'] = df_both['query_total_ipr_domain_length'] / df_both['ref_total_ipr_domain_length']

    fig = plt.figure(figsize=(18, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.35)

    # Plot 1: Proportional bias with regression line
    ax1 = fig.add_subplot(gs[0, :2])

    # Scatter with density coloring
    from matplotlib.colors import LogNorm
    h = ax1.hexbin(df_both['mean'], df_both['diff'],
                   gridsize=50, cmap='YlOrRd', mincnt=1,
                   norm=LogNorm())

    # Fit linear regression manually (numpy)
    coeffs = np.polyfit(df_both['mean'], df_both['diff'], 1)
    x_line = np.linspace(df_both['mean'].min(), df_both['mean'].max(), 100)
    y_line = coeffs[0] * x_line + coeffs[1]

    ax1.plot(x_line, y_line, 'b-', linewidth=3,
             label=f'Trend: y = {coeffs[0]:.3f}x + {coeffs[1]:.1f}')
    ax1.axhline(0, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Zero difference')
    ax1.axhline(df_both['diff'].mean(), color='red', linestyle='-', linewidth=2,
                label=f'Mean diff = {df_both["diff"].mean():.1f} aa')

    corr = df_both['mean'].corr(df_both['diff'])
    ax1.set_xlabel('Mean of Query and Reference (aa)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Difference (Query - Reference) (aa)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Proportional Bias Analysis\nCorrelation = {corr:.4f} (Strong!)',
                  fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    cb = plt.colorbar(h, ax=ax1)
    cb.set_label('Count', fontsize=10)

    # Plot 2: Ratio vs Reference (another view of proportional bias)
    ax2 = fig.add_subplot(gs[0, 2])

    # Filter extreme ratios for better visualization
    df_plot = df_both[df_both['ratio'] < 10].copy()

    ax2.scatter(df_plot['ref_total_ipr_domain_length'], df_plot['ratio'],
                alpha=0.3, s=15, c='steelblue', edgecolors='none')
    ax2.axhline(1.0, color='red', linestyle='--', linewidth=2, label='Ratio = 1')
    ax2.set_xlabel('Reference Length (aa)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Query/Reference Ratio', fontsize=11, fontweight='bold')
    ax2.set_title('Ratio vs Reference Length', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 5)

    # Plot 3: Correlation by class type
    ax3 = fig.add_subplot(gs[1, 0])

    class_types = sorted(df_both['class_type'].unique())
    correlations = []
    counts = []

    for ctype in class_types:
        subset = df_both[df_both['class_type'] == ctype]
        if len(subset) > 10:
            corr_val = subset['mean'].corr(subset['diff'])
            correlations.append(corr_val)
            counts.append(len(subset))
        else:
            correlations.append(0)
            counts.append(len(subset))

    colors_bar = ['red' if c > 0.7 else 'orange' if c > 0.4 else 'green' for c in correlations]
    bars = ax3.bar([f'T{ct}' for ct in class_types], correlations, color=colors_bar,
                   alpha=0.7, edgecolor='black', linewidth=1.5)

    # Add counts on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'n={count}', ha='center', va='bottom', fontsize=8)

    ax3.axhline(0.7, color='red', linestyle='--', linewidth=1, alpha=0.5, label='Strong (>0.7)')
    ax3.set_xlabel('Class Type', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Correlation (mean vs diff)', fontsize=11, fontweight='bold')
    ax3.set_title('Proportional Bias by Class Type', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.set_ylim(-0.1, 1.0)

    # Plot 4: Mean difference by class type
    ax4 = fig.add_subplot(gs[1, 1])

    mean_diffs = []
    for ctype in class_types:
        subset = df_both[df_both['class_type'] == ctype]
        mean_diffs.append(subset['diff'].mean())

    colors_bar2 = ['red' if d > 2000 else 'orange' if d > 500 else 'lightblue' if d > -500 else 'blue'
                   for d in mean_diffs]
    ax4.barh([f'Type {ct}' for ct in class_types], mean_diffs, color=colors_bar2,
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax4.axvline(0, color='black', linestyle='-', linewidth=2)
    ax4.set_xlabel('Mean Difference (Query - Ref) (aa)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Class Type', fontsize=11, fontweight='bold')
    ax4.set_title('Systematic Bias by Class Type', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')

    # Plot 5: Absolute difference distribution by class type
    ax5 = fig.add_subplot(gs[1, 2])

    data_violin = []
    labels_violin = []
    for ctype in class_types:
        subset = df_both[df_both['class_type'] == ctype]
        if len(subset) > 5:
            data_violin.append(subset['abs_diff'].values)
            labels_violin.append(f'T{ctype}')

    parts = ax5.violinplot(data_violin, positions=range(len(data_violin)),
                           showmeans=True, showmedians=True)
    ax5.set_xticks(range(len(labels_violin)))
    ax5.set_xticklabels(labels_violin)
    ax5.set_xlabel('Class Type', fontsize=11, fontweight='bold')
    ax5.set_ylabel('Absolute Difference |Query - Ref| (aa)', fontsize=11, fontweight='bold')
    ax5.set_title('Variability by Class Type', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')

    # Plot 6: Bland-Altman by class type (small multiples)
    for i, ctype in enumerate([0, 1, 2]):
        if i >= 3:
            break
        ax = fig.add_subplot(gs[2, i])
        subset = df_both[df_both['class_type'] == ctype]

        if len(subset) > 0:
            ax.scatter(subset['mean'], subset['diff'],
                      alpha=0.4, s=15, c='steelblue', edgecolors='none')
            ax.axhline(0, color='green', linestyle='--', linewidth=1.5)
            ax.axhline(subset['diff'].mean(), color='red', linestyle='-', linewidth=1.5)

            # Add regression line
            if len(subset) > 10:
                coeffs_sub = np.polyfit(subset['mean'], subset['diff'], 1)
                x_sub = np.linspace(subset['mean'].min(), subset['mean'].max(), 50)
                y_sub = coeffs_sub[0] * x_sub + coeffs_sub[1]
                ax.plot(x_sub, y_sub, 'b-', linewidth=2, alpha=0.7)

                corr_sub = subset['mean'].corr(subset['diff'])
                ax.text(0.05, 0.95, f'r={corr_sub:.3f}\nn={len(subset)}',
                       transform=ax.transAxes, fontsize=9, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))

            ax.set_xlabel('Mean (aa)', fontsize=10, fontweight='bold')
            ax.set_ylabel('Diff (aa)', fontsize=10, fontweight='bold')
            ax.set_title(f'Type {ctype}', fontsize=11, fontweight='bold')
            ax.grid(True, alpha=0.3)

    plt.savefig(f"{output_prefix}_proportional_bias.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_proportional_bias.png", file=sys.stderr)
    plt.close()

def plot_class_code_disagreement(df, output_prefix):
    """Identify and visualize class codes with most disagreement"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    df_both['mean'] = (df_both['query_total_ipr_domain_length'] +
                       df_both['ref_total_ipr_domain_length']) / 2
    df_both['diff'] = (df_both['query_total_ipr_domain_length'] -
                       df_both['ref_total_ipr_domain_length'])
    df_both['abs_diff'] = df_both['diff'].abs()
    df_both['percent_diff'] = 100 * df_both['diff'] / df_both['ref_total_ipr_domain_length']

    # Calculate metrics by class code
    class_code_stats = []
    for code in df_both['class_code'].unique():
        subset = df_both[df_both['class_code'] == code]

        if len(subset) >= 10:  # Only analyze codes with sufficient data
            stats = {
                'class_code': code,
                'count': len(subset),
                'mean_diff': subset['diff'].mean(),
                'mean_abs_diff': subset['abs_diff'].mean(),
                'std_diff': subset['diff'].std(),
                'median_diff': subset['diff'].median(),
                'correlation': subset['mean'].corr(subset['diff']),
                'mean_percent_diff': subset['percent_diff'].mean(),
                'query_mean': subset['query_total_ipr_domain_length'].mean(),
                'ref_mean': subset['ref_total_ipr_domain_length'].mean(),
            }
            class_code_stats.append(stats)

    df_stats = pd.DataFrame(class_code_stats)
    df_stats = df_stats.sort_values('mean_abs_diff', ascending=False)

    # Save statistics
    stats_file = f"{output_prefix}_class_code_stats.tsv"
    df_stats.to_csv(stats_file, sep='\t', index=False, float_format='%.2f')
    print(f"Saved statistics: {stats_file}", file=sys.stderr)

    fig = plt.figure(figsize=(20, 12))
    gs = GridSpec(3, 3, figure=fig, hspace=0.35, wspace=0.35)

    # Plot 1: Top disagreeing class codes (by absolute difference)
    ax1 = fig.add_subplot(gs[0, :])

    top_n = min(15, len(df_stats))
    df_top = df_stats.head(top_n).copy()

    x_pos = np.arange(len(df_top))
    colors_disc = ['red' if d > 3000 else 'orange' if d > 1500 else 'yellow'
                   for d in df_top['mean_abs_diff']]

    bars = ax1.bar(x_pos, df_top['mean_abs_diff'], color=colors_disc,
                   alpha=0.7, edgecolor='black', linewidth=1.5)

    # Add counts on bars
    for i, (bar, row) in enumerate(zip(bars, df_top.itertuples())):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'n={row.count}\n{row.mean_diff:+.0f}',
                ha='center', va='bottom', fontsize=8)

    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(df_top['class_code'], fontsize=11, fontweight='bold')
    ax1.set_xlabel('Class Code', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mean Absolute Difference |Query - Ref| (aa)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Top {top_n} Class Codes with Highest Disagreement\n(Number shows mean signed difference)',
                  fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # Plot 2: Correlation strength by class code
    ax2 = fig.add_subplot(gs[1, 0])

    df_corr = df_stats.sort_values('correlation', ascending=False).head(12)
    colors_corr = ['darkred' if c > 0.8 else 'red' if c > 0.7 else 'orange' if c > 0.5 else 'green'
                   for c in df_corr['correlation']]

    ax2.barh(df_corr['class_code'], df_corr['correlation'], color=colors_corr,
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax2.axvline(0.7, color='red', linestyle='--', linewidth=1.5, label='Strong (>0.7)')
    ax2.set_xlabel('Correlation (mean vs diff)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Class Code', fontsize=11, fontweight='bold')
    ax2.set_title('Proportional Bias Strength\n(Top 12 by correlation)', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3, axis='x')
    ax2.set_xlim(0, 1.0)

    # Plot 3: Query vs Reference mean lengths
    ax3 = fig.add_subplot(gs[1, 1])

    df_len = df_stats.sort_values('mean_abs_diff', ascending=False).head(10)

    x_pos3 = np.arange(len(df_len))
    width = 0.35

    ax3.bar(x_pos3 - width/2, df_len['query_mean'], width,
           label='Query', color='blue', alpha=0.7, edgecolor='black', linewidth=1.5)
    ax3.bar(x_pos3 + width/2, df_len['ref_mean'], width,
           label='Reference', color='red', alpha=0.7, edgecolor='black', linewidth=1.5)

    ax3.set_xticks(x_pos3)
    ax3.set_xticklabels(df_len['class_code'], rotation=45, ha='right')
    ax3.set_xlabel('Class Code', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Mean IPR Domain Length (aa)', fontsize=11, fontweight='bold')
    ax3.set_title('Query vs Reference Lengths\n(Top 10 disagreeing codes)', fontsize=12, fontweight='bold')
    ax3.legend(fontsize=10)
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Percent difference
    ax4 = fig.add_subplot(gs[1, 2])

    df_pct = df_stats.sort_values('mean_percent_diff', key=abs, ascending=False).head(10)
    colors_pct = ['red' if p > 0 else 'blue' for p in df_pct['mean_percent_diff']]

    ax4.barh(df_pct['class_code'], df_pct['mean_percent_diff'], color=colors_pct,
            alpha=0.7, edgecolor='black', linewidth=1.5)
    ax4.axvline(0, color='black', linestyle='-', linewidth=2)
    ax4.set_xlabel('Mean Percent Difference (%)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Class Code', fontsize=11, fontweight='bold')
    ax4.set_title('Percent Difference\n(Red: Query>Ref, Blue: Ref>Query)',
                  fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='x')

    # Plots 5-7: Detailed Bland-Altman for top 3 disagreeing codes
    top_3_codes = df_stats.head(3)['class_code'].tolist()

    for i, code in enumerate(top_3_codes):
        ax = fig.add_subplot(gs[2, i])
        subset = df_both[df_both['class_code'] == code]

        ax.scatter(subset['mean'], subset['diff'],
                  alpha=0.5, s=30, c='steelblue', edgecolors='black', linewidth=0.3)
        ax.axhline(0, color='green', linestyle='--', linewidth=2, alpha=0.7)
        ax.axhline(subset['diff'].mean(), color='red', linestyle='-', linewidth=2)

        # Regression line
        coeffs = np.polyfit(subset['mean'], subset['diff'], 1)
        x_line = np.linspace(subset['mean'].min(), subset['mean'].max(), 50)
        y_line = coeffs[0] * x_line + coeffs[1]
        ax.plot(x_line, y_line, 'b-', linewidth=2.5, alpha=0.8)

        corr = subset['mean'].corr(subset['diff'])
        mean_d = subset['diff'].mean()

        info_text = (f'Class: {code}\n'
                    f'n = {len(subset)}\n'
                    f'Mean Δ = {mean_d:+.0f} aa\n'
                    f'r = {corr:.3f}')

        ax.text(0.05, 0.95, info_text,
               transform=ax.transAxes, fontsize=9, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

        ax.set_xlabel('Mean (aa)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Difference (aa)', fontsize=10, fontweight='bold')
        ax.set_title(f'Bland-Altman: {code}', fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3)

    plt.savefig(f"{output_prefix}_class_code_disagreement.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_class_code_disagreement.png", file=sys.stderr)
    plt.close()

    return df_stats

def plot_outlier_analysis(df, output_prefix):
    """Identify and analyze extreme outliers"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    df_both['diff'] = (df_both['query_total_ipr_domain_length'] -
                       df_both['ref_total_ipr_domain_length'])
    df_both['abs_diff'] = df_both['diff'].abs()
    df_both['ratio'] = df_both['query_total_ipr_domain_length'] / df_both['ref_total_ipr_domain_length']

    # Define outliers (top 1% by absolute difference)
    threshold_99 = df_both['abs_diff'].quantile(0.99)
    df_outliers = df_both[df_both['abs_diff'] >= threshold_99].copy()

    # Save outlier list
    outlier_file = f"{output_prefix}_outliers.tsv"
    df_outliers_save = df_outliers[['old_gene', 'new_gene', 'class_code', 'class_type',
                                     'query_total_ipr_domain_length', 'ref_total_ipr_domain_length',
                                     'diff', 'abs_diff', 'ratio']].sort_values('abs_diff', ascending=False)
    df_outliers_save.to_csv(outlier_file, sep='\t', index=False, float_format='%.2f')
    print(f"Saved outliers: {outlier_file}", file=sys.stderr)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Outliers highlighted
    ax1 = axes[0, 0]
    ax1.scatter(df_both['query_total_ipr_domain_length'],
               df_both['ref_total_ipr_domain_length'],
               alpha=0.3, s=20, c='lightgray', edgecolors='none', label='Normal')
    ax1.scatter(df_outliers['query_total_ipr_domain_length'],
               df_outliers['ref_total_ipr_domain_length'],
               alpha=0.8, s=80, c='red', edgecolors='black', linewidth=1,
               marker='*', label=f'Outliers (top 1%, n={len(df_outliers)})')

    max_val = max(df_both['query_total_ipr_domain_length'].max(),
                  df_both['ref_total_ipr_domain_length'].max())
    ax1.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2)
    ax1.set_xlabel('Query Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Reference Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Outliers Highlighted (|diff| ≥ {threshold_99:.0f} aa)', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Outliers by class code
    ax2 = axes[0, 1]
    outlier_class_counts = df_outliers['class_code'].value_counts().head(10)
    colors_out = sns.color_palette("Reds_r", len(outlier_class_counts))

    ax2.barh(outlier_class_counts.index, outlier_class_counts.values,
            color=colors_out, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax2.set_xlabel('Number of Outliers', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Class Code', fontsize=12, fontweight='bold')
    ax2.set_title('Outlier Distribution by Class Code', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='x')

    # Plot 3: Outlier characteristics
    ax3 = axes[1, 0]

    outlier_types = df_outliers['class_type'].value_counts().sort_index()
    normal_types = df_both['class_type'].value_counts().sort_index()

    # Calculate percentage
    pct_outlier = (outlier_types / normal_types * 100).fillna(0)

    x_pos = np.arange(len(pct_outlier))
    ax3.bar(x_pos, pct_outlier.values, color='red', alpha=0.7,
           edgecolor='black', linewidth=1.5)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels([f'T{idx}' for idx in pct_outlier.index])
    ax3.set_xlabel('Class Type', fontsize=12, fontweight='bold')
    ax3.set_ylabel('% of genes that are outliers', fontsize=12, fontweight='bold')
    ax3.set_title('Outlier Frequency by Class Type', fontsize=13, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Outlier difference direction
    ax4 = axes[1, 1]

    query_higher = len(df_outliers[df_outliers['diff'] > 0])
    ref_higher = len(df_outliers[df_outliers['diff'] < 0])

    ax4.pie([query_higher, ref_higher],
           labels=[f'Query > Ref\n({query_higher})',
                  f'Ref > Query\n({ref_higher})'],
           colors=['blue', 'red'],
           autopct='%1.1f%%',
           startangle=90,
           explode=(0.05, 0.05),
           textprops={'fontsize': 12, 'fontweight': 'bold'})
    ax4.set_title('Direction of Extreme Disagreements', fontsize=13, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_outlier_analysis.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_outlier_analysis.png", file=sys.stderr)
    plt.close()

    print(f"\n  Top 5 outliers:", file=sys.stderr)
    for i, row in df_outliers_save.head(5).iterrows():
        print(f"    {row['new_gene']} vs {row['old_gene']}: "
              f"Δ={row['diff']:+.0f} aa (Q={row['query_total_ipr_domain_length']:.0f}, "
              f"R={row['ref_total_ipr_domain_length']:.0f}, code={row['class_code']})",
              file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Analyze proportional bias and class code disagreement in IPR domain lengths"
    )
    parser.add_argument('input', help="PAVprot output TSV file")
    parser.add_argument('--output-prefix', '-o', default='ipr_bias_analysis',
                       help="Output prefix for plot files")

    args = parser.parse_args()

    print(f"\nLoading data from: {args.input}", file=sys.stderr)
    df = load_data(args.input)
    print(f"Loaded {len(df)} entries", file=sys.stderr)

    # Create output directory
    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\nGenerating bias analysis plots...", file=sys.stderr)
    plot_proportional_bias_analysis(df, args.output_prefix)

    print("\nAnalyzing class code disagreement...", file=sys.stderr)
    df_stats = plot_class_code_disagreement(df, args.output_prefix)

    print("\nIdentifying outliers...", file=sys.stderr)
    plot_outlier_analysis(df, args.output_prefix)

    print("\n✓ All bias analysis plots generated successfully!", file=sys.stderr)
    print(f"\nCheck these files for detailed results:", file=sys.stderr)
    print(f"  - {args.output_prefix}_class_code_stats.tsv", file=sys.stderr)
    print(f"  - {args.output_prefix}_outliers.tsv", file=sys.stderr)

if __name__ == '__main__':
    main()
