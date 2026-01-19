#!/usr/bin/env python3
"""
Plot IPR domain lengths with distinct shapes for query vs reference
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
import sys
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

def load_data(input_file):
    """Load PAVprot output TSV file"""
    df = pd.read_csv(input_file, sep='\t')
    return df

def plot_scatter_with_shapes(df, output_prefix):
    """Scatter plot with different shapes for query and reference"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    fig, axes = plt.subplots(2, 2, figsize=(18, 16))

    # Plot 1: Query (circles) vs Reference (triangles) by class_code
    ax1 = axes[0, 0]
    class_codes = sorted(df_both['class_code'].unique())
    colors = sns.color_palette("husl", len(class_codes))
    color_map = dict(zip(class_codes, colors))

    for code in class_codes:
        subset = df_both[df_both['class_code'] == code]
        # Plot reference as triangles
        ax1.scatter(subset['ref_total_ipr_domain_length'],
                   subset['ref_total_ipr_domain_length'],
                   marker='^', s=80, alpha=0.6,
                   c=[color_map[code]], edgecolors='black', linewidth=0.5,
                   label=f'{code} (Ref)')
        # Plot query as circles
        ax1.scatter(subset['query_total_ipr_domain_length'],
                   subset['ref_total_ipr_domain_length'],
                   marker='o', s=60, alpha=0.6,
                   c=[color_map[code]], edgecolors='black', linewidth=0.3)

    max_val = max(df_both['query_total_ipr_domain_length'].max(),
                  df_both['ref_total_ipr_domain_length'].max())
    ax1.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2)

    ax1.set_xlabel('Domain Length (aa)\n○ Query    △ Reference on y-axis', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Reference Total IPR Domain Length (aa)', fontsize=11, fontweight='bold')
    ax1.set_title('Query (○) vs Reference (△) by Class Code', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    # Custom legend showing only reference triangles (query uses same colors)
    handles, labels = ax1.get_legend_handles_labels()
    ax1.legend(handles, [l.replace(' (Ref)', '') for l in labels],
              bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=7, ncol=1)

    # Plot 2: By class_type with shapes
    ax2 = axes[0, 1]
    class_types = sorted(df_both['class_type'].unique())
    colors_type = sns.color_palette("Set2", len(class_types))
    color_map_type = dict(zip(class_types, colors_type))

    class_type_labels = {
        0: 'T0', '0': 'T0',
        1: 'T1', '1': 'T1',
        2: 'T2', '2': 'T2',
        3: 'T3', '3': 'T3',
        4: 'T4', '4': 'T4',
        5: 'T5', '5': 'T5'
    }

    for ctype in class_types:
        subset = df_both[df_both['class_type'] == ctype]
        label = class_type_labels.get(ctype, f'T{ctype}')

        # Reference as squares
        ax2.scatter(subset['ref_total_ipr_domain_length'],
                   subset['ref_total_ipr_domain_length'],
                   marker='s', s=70, alpha=0.6,
                   c=[color_map_type[ctype]], edgecolors='black', linewidth=0.5,
                   label=f'{label} (Ref □)')
        # Query as diamonds
        ax2.scatter(subset['query_total_ipr_domain_length'],
                   subset['ref_total_ipr_domain_length'],
                   marker='D', s=50, alpha=0.6,
                   c=[color_map_type[ctype]], edgecolors='black', linewidth=0.3)

    ax2.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2)
    ax2.set_xlabel('Domain Length (aa)\n◇ Query    □ Reference on y-axis', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Reference Total IPR Domain Length (aa)', fontsize=11, fontweight='bold')
    ax2.set_title('Query (◇) vs Reference (□) by Class Type', fontsize=13, fontweight='bold')
    ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax2.grid(True, alpha=0.3)

    # Plot 3: Dual scatter showing both separately on same plot
    ax3 = axes[1, 0]

    # Sample if too many points
    sample_size = min(5000, len(df_both))
    df_sample = df_both.sample(n=sample_size, random_state=42)

    # Create index for x-axis (gene pair index)
    df_sample = df_sample.reset_index(drop=True)
    x_idx = np.arange(len(df_sample))

    # Plot reference as stars
    ax3.scatter(x_idx, df_sample['ref_total_ipr_domain_length'],
               marker='*', s=100, alpha=0.7, c='red',
               edgecolors='black', linewidth=0.3,
               label='Reference ★')
    # Plot query as circles
    ax3.scatter(x_idx, df_sample['query_total_ipr_domain_length'],
               marker='o', s=50, alpha=0.7, c='blue',
               edgecolors='black', linewidth=0.3,
               label='Query ●')

    ax3.set_xlabel(f'Gene Pair Index (random sample of {sample_size})', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Total IPR Domain Length (aa)', fontsize=11, fontweight='bold')
    ax3.set_title('Query (●) vs Reference (★) Side-by-Side', fontsize=13, fontweight='bold')
    ax3.legend(fontsize=11, loc='upper right')
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Ratio plot with shapes by emckmnj
    ax4 = axes[1, 1]

    df_both['ratio'] = df_both['query_total_ipr_domain_length'] / df_both['ref_total_ipr_domain_length']

    # Separate by emckmnj flag
    df_emckmnj_1 = df_both[df_both['emckmnj'] == 1]
    df_emckmnj_0 = df_both[df_both['emckmnj'] == 0]

    # emckmnj=1 as pentagons
    ax4.scatter(df_emckmnj_1['ref_total_ipr_domain_length'],
               df_emckmnj_1['ratio'],
               marker='p', s=70, alpha=0.6, c='green',
               edgecolors='black', linewidth=0.3,
               label='emckmnj=1 (⬟)')

    # emckmnj=0 as hexagons
    ax4.scatter(df_emckmnj_0['ref_total_ipr_domain_length'],
               df_emckmnj_0['ratio'],
               marker='h', s=70, alpha=0.6, c='orange',
               edgecolors='black', linewidth=0.3,
               label='emckmnj=0 (⬢)')

    ax4.axhline(1.0, color='red', linestyle='--', linewidth=2, label='Ratio = 1')
    ax4.set_xlabel('Reference Total IPR Domain Length (aa)', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Query/Reference Ratio', fontsize=11, fontweight='bold')
    ax4.set_title('Ratio vs Reference Length by emckmnj', fontsize=13, fontweight='bold')
    ax4.legend(fontsize=10)
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim(0, min(10, df_both['ratio'].quantile(0.99)))

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_shapes.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_shapes.png", file=sys.stderr)
    plt.close()

def plot_separate_distributions(df, output_prefix):
    """Plot query and reference as separate distributions"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Overlapping histograms with different styles
    ax1 = axes[0, 0]
    ax1.hist(df_both['query_total_ipr_domain_length'], bins=50, alpha=0.5,
            color='blue', edgecolor='black', linewidth=1.5, linestyle='-',
            label='Query', histtype='stepfilled')
    ax1.hist(df_both['ref_total_ipr_domain_length'], bins=50, alpha=0.5,
            color='red', edgecolor='black', linewidth=1.5, linestyle='--',
            label='Reference', histtype='stepfilled')
    ax1.set_xlabel('Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax1.set_title('Distribution: Query vs Reference', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)

    # Plot 2: KDE with different line styles (using seaborn)
    ax2 = axes[0, 1]
    sns.kdeplot(data=df_both['query_total_ipr_domain_length'], ax=ax2,
                linewidth=3, linestyle='-', color='blue', label='Query', fill=False)
    sns.kdeplot(data=df_both['ref_total_ipr_domain_length'], ax=ax2,
                linewidth=3, linestyle='--', color='red', label='Reference', fill=False)
    ax2.set_xlabel('Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Density', fontsize=12, fontweight='bold')
    ax2.set_title('Kernel Density: Query (—) vs Reference (---)', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)

    # Plot 3: Strip plot by class type with shapes
    ax3 = axes[1, 0]

    # Prepare long format
    df_long = pd.melt(df_both.sample(n=min(3000, len(df_both)), random_state=42),
                     id_vars=['class_type'],
                     value_vars=['query_total_ipr_domain_length', 'ref_total_ipr_domain_length'],
                     var_name='Type', value_name='IPR_Length')

    df_long['Type'] = df_long['Type'].replace({
        'query_total_ipr_domain_length': 'Query',
        'ref_total_ipr_domain_length': 'Reference'
    })

    # Manual strip plot with different markers
    class_types = sorted(df_long['class_type'].unique())
    x_positions = {ct: i for i, ct in enumerate(class_types)}

    for ct in class_types:
        subset_q = df_long[(df_long['class_type'] == ct) & (df_long['Type'] == 'Query')]
        subset_r = df_long[(df_long['class_type'] == ct) & (df_long['Type'] == 'Reference')]

        x_q = np.random.normal(x_positions[ct] - 0.15, 0.04, len(subset_q))
        x_r = np.random.normal(x_positions[ct] + 0.15, 0.04, len(subset_r))

        ax3.scatter(x_q, subset_q['IPR_Length'], marker='o', s=20, alpha=0.4,
                   c='blue', edgecolors='none')
        ax3.scatter(x_r, subset_r['IPR_Length'], marker='^', s=25, alpha=0.4,
                   c='red', edgecolors='none')

    ax3.set_xticks(list(x_positions.values()))
    ax3.set_xticklabels([f'T{ct}' for ct in class_types])
    ax3.set_xlabel('Class Type', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax3.set_title('Query (●) vs Reference (△) Strip Plot', fontsize=14, fontweight='bold')

    # Custom legend
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker='o', color='w',
                             markerfacecolor='blue', markersize=8, label='Query'),
                      Line2D([0], [0], marker='^', color='w',
                             markerfacecolor='red', markersize=9, label='Reference')]
    ax3.legend(handles=legend_elements, fontsize=11)
    ax3.grid(True, alpha=0.3, axis='y')

    # Plot 4: Box plot comparison by class code (top 8)
    ax4 = axes[1, 1]

    top_codes = df_both['class_code'].value_counts().head(8).index.tolist()
    df_top = df_both[df_both['class_code'].isin(top_codes)]

    # Prepare data
    data_q = [df_top[df_top['class_code'] == code]['query_total_ipr_domain_length'].values
              for code in top_codes]
    data_r = [df_top[df_top['class_code'] == code]['ref_total_ipr_domain_length'].values
              for code in top_codes]

    positions_q = np.arange(len(top_codes)) * 2 - 0.4
    positions_r = np.arange(len(top_codes)) * 2 + 0.4

    bp1 = ax4.boxplot(data_q, positions=positions_q, widths=0.6,
                     patch_artist=True, showfliers=False,
                     boxprops=dict(facecolor='lightblue', edgecolor='blue', linewidth=2),
                     medianprops=dict(color='darkblue', linewidth=2),
                     whiskerprops=dict(color='blue', linewidth=1.5),
                     capprops=dict(color='blue', linewidth=1.5))

    bp2 = ax4.boxplot(data_r, positions=positions_r, widths=0.6,
                     patch_artist=True, showfliers=False,
                     boxprops=dict(facecolor='lightcoral', edgecolor='red', linewidth=2, linestyle='--'),
                     medianprops=dict(color='darkred', linewidth=2),
                     whiskerprops=dict(color='red', linewidth=1.5, linestyle='--'),
                     capprops=dict(color='red', linewidth=1.5, linestyle='--'))

    ax4.set_xticks(np.arange(len(top_codes)) * 2)
    ax4.set_xticklabels(top_codes)
    ax4.set_xlabel('Class Code (Top 8)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Total IPR Domain Length (aa)', fontsize=12, fontweight='bold')
    ax4.set_title('Box Plot: Query (─) vs Reference (---)', fontsize=14, fontweight='bold')

    # Custom legend
    legend_elements = [Patch(facecolor='lightblue', edgecolor='blue', linewidth=2, label='Query'),
                      Patch(facecolor='lightcoral', edgecolor='red', linewidth=2, linestyle='--', label='Reference')]
    ax4.legend(handles=legend_elements, fontsize=11)
    ax4.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_distributions_separated.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_distributions_separated.png", file=sys.stderr)
    plt.close()

def main():
    parser = argparse.ArgumentParser(
        description="Plot IPR domain lengths with distinct shapes/markers for query vs reference"
    )
    parser.add_argument('input', help="PAVprot output TSV file")
    parser.add_argument('--output-prefix', '-o', default='ipr_shapes',
                       help="Output prefix for plot files")

    args = parser.parse_args()

    print(f"\nLoading data from: {args.input}", file=sys.stderr)
    df = load_data(args.input)
    print(f"Loaded {len(df)} entries", file=sys.stderr)

    # Create output directory
    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("\nGenerating plots with distinct shapes...", file=sys.stderr)
    plot_scatter_with_shapes(df, args.output_prefix)
    plot_separate_distributions(df, args.output_prefix)

    print("\n✓ All shape-based plots generated successfully!", file=sys.stderr)

if __name__ == '__main__':
    main()
