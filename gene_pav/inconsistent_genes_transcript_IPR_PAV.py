#!/usr/bin/env python3
"""
Analyze and visualize genes with transcripts in different IPR domain presence/absence categories

This script can process:
1. Original PAVprot output file (synonym_mapping_liftover_gffcomp.tsv)
   - Filters to find gene pairs with inconsistent transcript quadrants
2. Pre-filtered inconsistent genes file (*_inconsistent_genes.tsv)
   - Directly analyzes the inconsistent genes

Generates:
- Summary statistics
- Detailed TSV output (if starting from original file)
- Summary TSV with quadrant combinations
- Comprehensive visualization plots
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import sys
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300


def detect_file_type(df):
    """Detect if input is original file or filtered inconsistent genes file"""
    # Check if 'quadrant' column exists (indicates pre-filtered file)
    if 'quadrant' in df.columns:
        return 'filtered'
    else:
        return 'original'


def assign_quadrants(df):
    """Assign quadrant categories based on IPR domain presence/absence"""
    df_assigned = df.copy()

    df_assigned['quadrant'] = 'Present in both'

    df_assigned.loc[df_assigned['query_total_ipr_domain_length'].isna() &
                    df_assigned['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Absent in both'

    df_assigned.loc[df_assigned['query_total_ipr_domain_length'].isna() &
                    (df_assigned['ref_total_ipr_domain_length'] > 0), 'quadrant'] = 'Ref only'

    df_assigned.loc[(df_assigned['query_total_ipr_domain_length'] > 0) &
                    df_assigned['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Query only'

    return df_assigned


def filter_inconsistent_genes(df):
    """Filter for gene pairs with transcripts in multiple quadrants"""

    # Assign quadrants if not already assigned
    if 'quadrant' not in df.columns:
        df = assign_quadrants(df)

    # Find gene pairs with multiple quadrants
    gene_pair_quadrants = df.groupby(['ref_gene', 'query_gene'])['quadrant'].apply(
        lambda x: list(x.unique())
    ).reset_index()
    gene_pair_quadrants['num_quadrants'] = gene_pair_quadrants['quadrant'].apply(len)

    # Filter to only those with multiple quadrants
    inconsistent_gene_pairs = gene_pair_quadrants[gene_pair_quadrants['num_quadrants'] > 1]

    if len(inconsistent_gene_pairs) == 0:
        return None, None

    # Get detailed information for these genes
    inconsistent_details = []
    for _, row in inconsistent_gene_pairs.iterrows():
        ref_g = row['ref_gene']
        qry_g = row['query_gene']
        subset = df[(df['ref_gene'] == ref_g) & (df['query_gene'] == qry_g)]
        inconsistent_details.append(subset)

    df_inconsistent = pd.concat(inconsistent_details, ignore_index=True)
    df_inconsistent = df_inconsistent.sort_values(['ref_gene', 'query_gene', 'quadrant'])

    return df_inconsistent, inconsistent_gene_pairs


def create_summary_table(df_inconsistent):
    """Create summary table with quadrant combinations"""

    # Group by gene pairs
    gene_pairs = df_inconsistent.groupby(['ref_gene', 'query_gene'])

    summary_data = []
    for (ref_g, qry_g), group in gene_pairs:
        quadrants = sorted(group['quadrant'].unique())
        quadrant_counts = group['quadrant'].value_counts().to_dict()

        summary_data.append({
            'ref_gene': ref_g,
            'query_gene': qry_g,
            'num_transcripts': len(group),
            'quadrants': ', '.join(quadrants),
            'count_Present_in_both': quadrant_counts.get('Present in both', 0),
            'count_Absent_in_both': quadrant_counts.get('Absent in both', 0),
            'count_Ref_only': quadrant_counts.get('Ref only', 0),
            'count_Query_only': quadrant_counts.get('Query only', 0)
        })

    df_summary = pd.DataFrame(summary_data)
    return df_summary


def print_statistics(df_inconsistent, df_summary, ref_prefix, qry_prefix):
    """Print detailed statistics"""

    print(f"\n{'='*80}", file=sys.stderr)
    print(f"INCONSISTENT GENES ANALYSIS", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)

    print(f"\nGene pairs with inconsistent transcript quadrants: {len(df_summary)}", file=sys.stderr)
    print(f"Total transcript pairs: {len(df_inconsistent)}", file=sys.stderr)

    # Unique genes
    unique_ref = df_inconsistent['ref_gene'].nunique()
    unique_qry = df_inconsistent['query_gene'].nunique()
    print(f"\nUnique genes involved:", file=sys.stderr)
    print(f"  {ref_prefix} genes: {unique_ref}", file=sys.stderr)
    print(f"  {qry_prefix} genes: {unique_qry}", file=sys.stderr)
    print(f"  Total: {unique_ref + unique_qry}", file=sys.stderr)

    # Quadrant distribution
    print(f"\nTranscript distribution across quadrants:", file=sys.stderr)
    quadrant_counts = df_inconsistent['quadrant'].value_counts()
    for quadrant, count in quadrant_counts.items():
        print(f"  {quadrant}: {count}", file=sys.stderr)

    # Quadrant combinations
    print(f"\nQuadrant combination frequencies:", file=sys.stderr)
    combo_counts = df_summary['quadrants'].value_counts()
    for combo, count in combo_counts.items():
        print(f"  {combo}: {count} gene pairs", file=sys.stderr)

    # Transcripts per gene pair statistics
    print(f"\nTranscripts per gene pair statistics:", file=sys.stderr)
    print(f"  Mean: {df_summary['num_transcripts'].mean():.2f}", file=sys.stderr)
    print(f"  Median: {df_summary['num_transcripts'].median():.0f}", file=sys.stderr)
    print(f"  Range: {df_summary['num_transcripts'].min()}-{df_summary['num_transcripts'].max()}", file=sys.stderr)


def plot_comprehensive_analysis(df_inconsistent, df_summary, output_prefix, ref_prefix, qry_prefix):
    """Create comprehensive visualization with multiple panels"""

    # Create figure with 4 subplots
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    # ===== Plot 1: Quadrant combination distribution =====
    ax1 = fig.add_subplot(gs[0, 0])

    quadrant_combo_counts = df_summary['quadrants'].value_counts().sort_values(ascending=True)

    colors_map = {
        'Absent in both, Present in both': '#FFA500',
        'Present in both, Ref only': '#FF6B6B',
        'Present in both, Query only': '#4ECDC4',
        'Absent in both, Ref only': '#95E1D3',
        'Absent in both, Query only': '#F38181',
        'Absent in both, Present in both, Ref only': '#9B59B6',
        'Absent in both, Present in both, Query only': '#E67E22',
        'Present in both, Query only, Ref only': '#3498DB',
    }

    bar_colors = [colors_map.get(combo, '#CCCCCC') for combo in quadrant_combo_counts.index]

    ax1.barh(range(len(quadrant_combo_counts)), quadrant_combo_counts.values,
             color=bar_colors, edgecolor='black', linewidth=1.5)
    ax1.set_yticks(range(len(quadrant_combo_counts)))
    ax1.set_yticklabels(quadrant_combo_counts.index, fontsize=11)
    ax1.set_xlabel('Number of Gene Pairs', fontsize=13, fontweight='bold')
    ax1.set_title('Distribution of Quadrant Combinations', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)

    for i, v in enumerate(quadrant_combo_counts.values):
        ax1.text(v + 0.3, i, str(v), va='center', fontsize=10, fontweight='bold')

    # ===== Plot 2: Overall transcript distribution =====
    ax2 = fig.add_subplot(gs[0, 1])

    quadrant_counts = df_inconsistent['quadrant'].value_counts()
    quadrant_colors = {'Present in both': 'green', 'Absent in both': 'gray',
                      'Ref only': 'red', 'Query only': 'blue'}

    colors = [quadrant_colors.get(q, 'gray') for q in quadrant_counts.index]

    bars = ax2.bar(range(len(quadrant_counts)), quadrant_counts.values,
                   color=colors, edgecolor='black', linewidth=1.5, alpha=0.7)
    ax2.set_xticks(range(len(quadrant_counts)))
    ax2.set_xticklabels(quadrant_counts.index, rotation=45, ha='right', fontsize=11)
    ax2.set_ylabel('Number of Transcripts', fontsize=13, fontweight='bold')
    ax2.set_title('Transcript Distribution Across Quadrants', fontsize=14, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    for i, (bar, count) in enumerate(zip(bars, quadrant_counts.values)):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # ===== Plot 3: Top gene pairs with stacked bars =====
    ax3 = fig.add_subplot(gs[1, :])

    # Get top 20 gene pairs by transcript count
    top_gene_pairs = df_summary.nlargest(min(20, len(df_summary)), 'num_transcripts')

    # Create labels
    gene_pair_labels = []
    for _, row in top_gene_pairs.iterrows():
        ref_short = row['ref_gene'].split('-')[-1].split('_')[0][-10:]
        qry_short = row['query_gene'].split('_')[0][-10:]
        gene_pair_labels.append(f"{ref_short}\nvs\n{qry_short}")

    # Stacked bar chart
    x_pos = np.arange(len(top_gene_pairs))
    bar_width = 0.7

    quadrant_cols = ['count_Present_in_both', 'count_Absent_in_both',
                     'count_Ref_only', 'count_Query_only']
    quadrant_labels = ['Present in both', 'Absent in both', 'Ref only', 'Query only']
    plot_colors = ['green', 'gray', 'red', 'blue']

    bottom = np.zeros(len(top_gene_pairs))
    for col, label, color in zip(quadrant_cols, quadrant_labels, plot_colors):
        values = top_gene_pairs[col].values
        ax3.bar(x_pos, values, bar_width, label=label, color=color,
                bottom=bottom, edgecolor='black', linewidth=0.5, alpha=0.8)

        # Add labels for non-zero values
        for i, (val, bot) in enumerate(zip(values, bottom)):
            if val > 0:
                ax3.text(i, bot + val/2, str(int(val)),
                        ha='center', va='center', fontsize=8, fontweight='bold')

        bottom += values

    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(gene_pair_labels, fontsize=9)
    ax3.set_ylabel('Number of Transcripts', fontsize=13, fontweight='bold')
    ax3.set_xlabel('Gene Pairs (Ranked by Total Transcript Count)', fontsize=13, fontweight='bold')
    ax3.set_title(f'Quadrant Distribution for Top {len(top_gene_pairs)} Gene Pairs with Most Transcripts',
                  fontsize=14, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=11, framealpha=0.9)
    ax3.grid(axis='y', alpha=0.3)

    plt.savefig(f"{output_prefix}_comprehensive_analysis.png", bbox_inches='tight')
    print(f"Saved comprehensive analysis plot: {output_prefix}_comprehensive_analysis.png", file=sys.stderr)
    plt.close()


def plot_gene_level_details(df_inconsistent, df_summary, output_prefix, ref_prefix, qry_prefix):
    """Create detailed plot showing individual transcript IPR domain lengths"""

    # Select top gene pairs for detailed view
    top_n = min(12, len(df_summary))
    top_gene_pairs = df_summary.nlargest(top_n, 'num_transcripts')

    # Create subplots
    ncols = 3
    nrows = (top_n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 5*nrows))
    axes = axes.flatten() if nrows > 1 else [axes] if top_n == 1 else axes

    quadrant_colors = {'Present in both': 'green', 'Absent in both': 'gray',
                      'Ref only': 'red', 'Query only': 'blue'}

    for idx, (_, row) in enumerate(top_gene_pairs.iterrows()):
        if idx >= len(axes):
            break

        ax = axes[idx]

        ref_g = row['ref_gene']
        qry_g = row['query_gene']

        # Get transcripts for this gene pair
        subset = df_inconsistent[(df_inconsistent['ref_gene'] == ref_g) &
                                 (df_inconsistent['query_gene'] == qry_g)]

        # Plot each transcript
        for i, (_, transcript) in enumerate(subset.iterrows()):
            query_len = transcript['query_total_ipr_domain_length']
            ref_len = transcript['ref_total_ipr_domain_length']
            quadrant = transcript['quadrant']

            # Handle NaN values for plotting
            query_len_plot = 0 if pd.isna(query_len) else query_len
            ref_len_plot = 0 if pd.isna(ref_len) else ref_len

            # Add jitter for zero values
            if query_len_plot == 0:
                query_len_plot = np.random.uniform(-5, 5)
            if ref_len_plot == 0:
                ref_len_plot = np.random.uniform(-5, 5)

            ax.scatter(query_len_plot, ref_len_plot,
                      c=quadrant_colors[quadrant], s=100, alpha=0.7,
                      edgecolors='black', linewidth=1.5)

        # Add diagonal line
        max_val = max(
            subset['query_total_ipr_domain_length'].max() if not subset['query_total_ipr_domain_length'].isna().all() else 0,
            subset['ref_total_ipr_domain_length'].max() if not subset['ref_total_ipr_domain_length'].isna().all() else 0
        )
        if max_val > 0:
            ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, linewidth=1)

        # Format axes
        ref_short = ref_g.split('-')[-1][:15]
        qry_short = qry_g[:15]
        ax.set_title(f"{ref_short} vs {qry_short}\n({len(subset)} transcripts)",
                    fontsize=10, fontweight='bold')
        ax.set_xlabel(f'{qry_prefix} IPR length (aa)', fontsize=9)
        ax.set_ylabel(f'{ref_prefix} IPR length (aa)', fontsize=9)
        ax.grid(True, alpha=0.3)

    # Hide unused subplots
    for idx in range(len(top_gene_pairs), len(axes)):
        axes[idx].axis('off')

    # Add legend
    handles = [plt.Line2D([0], [0], marker='o', color='w',
                         markerfacecolor=color, markersize=10, label=label,
                         markeredgecolor='black', markeredgewidth=1)
              for label, color in quadrant_colors.items()]
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(0.5, 0.98),
              ncol=4, fontsize=11, frameon=True, fancybox=True)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(f"{output_prefix}_gene_level_details.png", bbox_inches='tight')
    print(f"Saved gene-level details plot: {output_prefix}_gene_level_details.png", file=sys.stderr)
    plt.close()


def auto_detect_prefixes(df):
    """Auto-detect genome prefixes from gene names"""

    def extract_prefix(gene_name):
        if pd.isna(gene_name):
            return None
        gene_str = str(gene_name)
        if gene_str.startswith('gene-'):
            gene_str = gene_str[5:]
        if '_' in gene_str:
            return gene_str.split('_')[0]
        if '-' in gene_str:
            return gene_str.split('-')[0]
        return gene_str[:10]

    ref_prefixes = df['ref_gene'].dropna().apply(extract_prefix).value_counts()
    query_prefixes = df['query_gene'].dropna().apply(extract_prefix).value_counts()

    if len(ref_prefixes) == 0 or len(query_prefixes) == 0:
        return "Reference", "Query"

    return ref_prefixes.index[0], query_prefixes.index[0]


def main():
    parser = argparse.ArgumentParser(
        description="Analyze genes with transcripts in different IPR domain presence/absence categories"
    )
    parser.add_argument('input', help="Input TSV file (original PAVprot output or pre-filtered inconsistent genes)")
    parser.add_argument('--output-prefix', '-o', default='inconsistent_genes_analysis',
                       help="Output prefix for files (default: inconsistent_genes_analysis)")
    parser.add_argument('--ref-qry-prefix', default=None,
                       help="Comma or space-separated reference and query genome prefixes (auto-detected if not provided)")

    args = parser.parse_args()

    # Load data
    print(f"\nLoading data from: {args.input}", file=sys.stderr)
    df = pd.read_csv(args.input, sep='\t')
    print(f"Loaded {len(df)} rows", file=sys.stderr)

    # Auto-detect or parse genome prefixes
    if args.ref_qry_prefix:
        if ',' in args.ref_qry_prefix:
            prefixes = [p.strip() for p in args.ref_qry_prefix.split(',')]
        else:
            prefixes = args.ref_qry_prefix.split()

        if len(prefixes) != 2:
            print(f"Error: --ref-qry-prefix must contain exactly 2 values", file=sys.stderr)
            sys.exit(1)

        ref_prefix, qry_prefix = prefixes
        print(f"Using provided prefixes: Ref='{ref_prefix}', Query='{qry_prefix}'", file=sys.stderr)
    else:
        ref_prefix, qry_prefix = auto_detect_prefixes(df)
        print(f"Auto-detected prefixes: Ref='{ref_prefix}', Query='{qry_prefix}'", file=sys.stderr)

    # Detect file type and process
    file_type = detect_file_type(df)
    print(f"Detected file type: {file_type}", file=sys.stderr)

    if file_type == 'original':
        # Filter for inconsistent genes
        print("\nFiltering for genes with inconsistent transcript quadrants...", file=sys.stderr)
        df_inconsistent, gene_pairs_info = filter_inconsistent_genes(df)

        if df_inconsistent is None:
            print("\nNo genes with transcripts in multiple quadrants found.", file=sys.stderr)
            print("All gene pairs have consistent quadrant assignments across transcripts.", file=sys.stderr)
            return

        # Save detailed output
        output_file = f"{args.output_prefix}_detailed.tsv"
        df_inconsistent.to_csv(output_file, sep='\t', index=False)
        print(f"Saved detailed data: {output_file}", file=sys.stderr)
    else:
        # Already filtered
        df_inconsistent = df
        print("\nProcessing pre-filtered inconsistent genes data...", file=sys.stderr)

    # Create summary table
    df_summary = create_summary_table(df_inconsistent)

    # Save summary
    summary_file = f"{args.output_prefix}_summary.tsv"
    df_summary.to_csv(summary_file, sep='\t', index=False)
    print(f"Saved summary: {summary_file}", file=sys.stderr)

    # Print statistics
    print_statistics(df_inconsistent, df_summary, ref_prefix, qry_prefix)

    # Create visualizations
    print(f"\nGenerating visualizations...", file=sys.stderr)
    plot_comprehensive_analysis(df_inconsistent, df_summary, args.output_prefix, ref_prefix, qry_prefix)
    plot_gene_level_details(df_inconsistent, df_summary, args.output_prefix, ref_prefix, qry_prefix)

    print(f"\n{'='*80}", file=sys.stderr)
    print(f"✓ Analysis complete!", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)


if __name__ == '__main__':
    main()
