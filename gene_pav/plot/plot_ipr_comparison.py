#!/usr/bin/env python3
"""
Plot query vs reference total IPR domain lengths from PAVprot output
"""

from ctypes import sizeof
from tokenize import group
from turtle import title
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
import sys
from pathlib import Path

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300

def load_pavprot_data(input_file):
    """Load PAVprot output TSV file"""
    try:
        df = pd.read_csv(input_file, sep='\t')
        df = df.copy()
        df['class_type'] = df['class_type'].replace('a', '=', regex=True)
        
        print(df.head)

        # Check if required columns exist
        required_cols = ['query_total_ipr_domain_length', 'ref_total_ipr_domain_length']
        missing = [col for col in required_cols if col not in df.columns]

        if missing:
            print(f"Error: Missing required columns: {missing}", file=sys.stderr)
            print(f"Available columns: {df.columns.tolist()}", file=sys.stderr)
            sys.exit(1)
        # print(df.head)
        # print(df_new.head)

        return df
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        sys.exit(1)

def plot_scatter_by_class_type(df, output_prefix, ref_genome_prefix, qry_genome_prefix):
    """Create scatter plot colored by class_type"""

    # Filter out zeros for better visualization
    df_nonzero = df[(df['query_total_ipr_domain_length'] > 0) &
                    (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_nonzero) == 0:
        print("Warning: No non-zero IPR domain data to plot", file=sys.stderr)
        return

    fig, ax = plt.subplots(figsize=(12, 10))

    # Get unique class types and assign colors
    class_type = df_nonzero['class_type'].unique()
    colors = sns.color_palette("colorblind", len(class_type))
    color_map = dict(zip(class_type, colors))

    # Plot each class type
    for code in sorted(class_type):
        subset = df_nonzero[df_nonzero['class_type'] == code]
        ax.scatter(subset['query_total_ipr_domain_length'],
                  subset['ref_total_ipr_domain_length'],
                  c=[color_map[code]],
                  label=f"{code} (n={len(subset)})",
                  alpha=0.6,
                  s=90,
                  edgecolors='black',
                  linewidth=0.3)

    # Add diagonal line (perfect match)
    max_val = max(df_nonzero['query_total_ipr_domain_length'].max(),
                  df_nonzero['ref_total_ipr_domain_length'].max())
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2, label='y=x (perfect match)')

    # Calculate correlation
    corr = df_nonzero['query_total_ipr_domain_length'].corr(
        df_nonzero['ref_total_ipr_domain_length'])

    if ref_genome_prefix:
        ax.set_xlabel(f'{qry_genome_prefix} total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_ylabel(f'{ref_genome_prefix} total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_title(f'{qry_genome_prefix} vs {ref_genome_prefix} gene pair total IPR domain length\n' +
                    f'(Pearson r = {corr:.3f}, n = {len(df_nonzero)})',
                    fontsize=16, fontweight='bold')
    else:
        ax.set_xlabel('Query total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Reference total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_title(f'Query vs Reference gene pair total IPR domain length \n' +
                f'Pearson r = {corr:.3f}, n = {len(df_nonzero)}',
                fontsize=16, fontweight='bold')

    ax.legend(bbox_to_anchor=(0.75, 0.3), loc='upper left', 
              fontsize=14, 
              title="gffcompare class type",
              title_fontsize = 14)
    ax.get_legend().get_title().set_fontweight("bold")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_by_class_type.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_by_class_type.png", file=sys.stderr)
    plt.close()


def plot_density_hexbin(df, output_prefix, ref_genome_prefix, qry_genome_prefix):
    """Create hexbin density plot for overall pattern"""

    df_nonzero = df[(df['query_total_ipr_domain_length'] > 0) &
                    (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_nonzero) == 0:
        return

    fig, ax = plt.subplots(figsize=(10, 9))

    hexbin = ax.hexbin(df_nonzero['query_total_ipr_domain_length'],
                       df_nonzero['ref_total_ipr_domain_length'],
                       gridsize=50,
                       cmap='YlOrRd',
                       mincnt=1,
                       edgecolors='face',
                       linewidths=0.2)

    max_val = max(df_nonzero['query_total_ipr_domain_length'].max(),
                  df_nonzero['ref_total_ipr_domain_length'].max())
    ax.plot([0, max_val], [0, max_val], 'b--', alpha=0.7, linewidth=2, label='y=x (perfect match)')

    corr = df_nonzero['query_total_ipr_domain_length'].corr(
        df_nonzero['ref_total_ipr_domain_length'])

    if ref_genome_prefix:
        ax.set_xlabel(f'{qry_genome_prefix} total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_ylabel(f'{ref_genome_prefix} total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_title(f'{qry_genome_prefix} vs {ref_genome_prefix} gene pair total IPR domain length\n' +
                    f'(Pearson r = {corr:.3f}, n = {len(df_nonzero)})',
                    fontsize=16, fontweight='bold')
    else:
        ax.set_xlabel('Query total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Reference total IPR domain length (aa)', fontsize=14, fontweight='bold')
        ax.set_title(f'Query vs Reference gene pair total IPR domain length \n' +
                f'Pearson r = {corr:.3f}, n = {len(df_nonzero)}',
                fontsize=16, fontweight='bold')

    # ax.legend(bbox_to_anchor=(0.75, 0.3), loc='upper left', 
    #           fontsize=14, 
    #           title="gffcompare class type",
    #           title_fontsize = 14)
    # ax.get_legend().get_title().set_fontweight("bold")

    cb = plt.colorbar(hexbin, ax=ax)
    cb.set_label('Count', fontsize=14, fontweight='bold')
    ax.legend(fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_density_hexbin.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_density_hexbin.png", file=sys.stderr)
    plt.close()
    
def plot_log_scale(df, output_prefix, ref_genome_prefix, qry_genome_prefix):
    """Log-log scale plot for wide-range data"""

    df_both = df[(df['query_total_ipr_domain_length'] > 0) &
                 (df['ref_total_ipr_domain_length'] > 0)].copy()

    if len(df_both) == 0:
        return

    # fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig, ax1 = plt.subplots(figsize=(12, 10))


    # Log-log scatter colored by class_type
    class_types = df_both['class_type'].unique()
    colors = sns.color_palette("husl", len(class_types))
    color_map = dict(zip(class_types, colors))

    for code in sorted(class_types):
        subset = df_both[df_both['class_type'] == code]
        ax1.scatter(subset['query_total_ipr_domain_length'],
                   subset['ref_total_ipr_domain_length'],
                   c=[color_map[code]], label=f'{code}',
                   alpha=0.6, s=60, edgecolors='black', linewidth=0.2)

    # Diagonal line
    min_val = min(df_both['query_total_ipr_domain_length'].min(),
                  df_both['ref_total_ipr_domain_length'].min())
    max_val = max(df_both['query_total_ipr_domain_length'].max(),
                  df_both['ref_total_ipr_domain_length'].max())
    ax1.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, linewidth=2)

    ax1.set_xscale('log')
    ax1.set_yscale('log')
    if ref_genome_prefix:
            ax1.set_xlabel(f'{qry_genome_prefix} Total IPR Domain Length (aa, log scale)', fontsize=14, fontweight='bold')
            ax1.set_ylabel(f'{ref_genome_prefix} Total IPR Domain Length (aa, log scale)', fontsize=14, fontweight='bold')
    else:
        ax1.set_xlabel('Query Total IPR Domain Length (aa, log scale)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Reference Total IPR Domain Length (aa, log scale)', fontsize=14, fontweight='bold')
        
    ax1.set_title('Log-Log scale plot', fontsize=14, fontweight='bold')
    ax1.legend(bbox_to_anchor=(0.86, 0.26), 
              loc='upper left', 
              fontsize=14,
              title="gffcompare\nclass type",
              title_fontsize = 14,
              markerscale=1.5)
    ax1.get_legend().get_title().set_fontweight("bold")
    ax1.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_loglog_scale.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_loglog_scale.png", file=sys.stderr)
    plt.close()


def plot_four_quadrants(df,output_prefix, ref_genome_prefix, qry_genome_prefix):
    """Create a four-quadrant plot showing presence/absence patterns at transcript level"""

    fig, ax2 = plt.subplots(figsize=(12, 10))

    # Define quadrants based on presence/absence at transcript level
    df_plot = df.copy()

    df_plot['quadrant'] = 'Present in both'

    df_plot.loc[df_plot['query_total_ipr_domain_length'].isna() &
                df_plot['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Absent in both'

    df_plot.loc[df_plot['query_total_ipr_domain_length'].isna() &
                (df_plot['ref_total_ipr_domain_length'] > 0), 'quadrant'] = 'Ref only'

    df_plot.loc[(df_plot['query_total_ipr_domain_length'] > 0) &
                df_plot['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Query only'

    # Keep all transcript pairs (include transcript IDs in selection)
    df_plot = df_plot[["ref_gene", "ref_transcript", "query_gene", "query_transcript",
                       "class_type", "query_total_ipr_domain_length",
                       "ref_total_ipr_domain_length", "quadrant"]].drop_duplicates()

    print(f"\nTranscript-level analysis: {len(df_plot)} transcript pairs", file=sys.stderr)
    print(f"Transcript-level quadrant distribution:", file=sys.stderr)
    print(df_plot['quadrant'].value_counts().to_string(), file=sys.stderr)
    quadrant_colors = {
        'Present in both': 'green',
        'Absent in both': 'gray',
        'Ref only': 'red',
        'Query only': 'blue'
    }

    for quad, color in quadrant_colors.items():
        subset = df_plot[df_plot['quadrant'] == quad]
        # Add small jitter to zeros for visibility
        x = subset['query_total_ipr_domain_length'].copy()
        y = subset['ref_total_ipr_domain_length'].copy()
        

        if quad == 'Absent in both':
            # Jitter for both absent
            x = np.random.normal(0, 5, len(subset))
            y = np.random.normal(0, 5, len(subset))
        elif quad == 'Ref only':
            # Jitter for query=0
            x = np.random.normal(0, 5, len(subset))
        elif quad == 'Query only':
            # Jitter for ref=0
            y = np.random.normal(0, 5, len(subset))

        ax2.scatter(x, y,
                  c=color,
                  label=f"{quad} (n={len(subset)})",
                  alpha=0.5,
                  s=40,
                  edgecolors='black',
                  linewidth=0.2)

    max_val = max(df['query_total_ipr_domain_length'].max(),
                  df['ref_total_ipr_domain_length'].max())
    ax2.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2, label='y=x')

    if ref_genome_prefix:
        ax2.set_xlabel(f'{qry_genome_prefix} Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')
        ax2.set_ylabel(f'{ref_genome_prefix} Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')
    else:
        ax2.set_xlabel('Query Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Reference Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')
        
    ax2.set_title('Presence/Absence Patterns of IPR Domains', fontsize=16, fontweight='bold')

    ax2.legend(fontsize=14)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_quadrants.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_quadrants.png", file=sys.stderr)
    plt.close()


def plot_four_quadrants_gene_level(df, output_prefix, ref_genome_prefix, qry_genome_prefix):
    """Create a four-quadrant plot showing presence/absence patterns at gene level"""

    fig, ax2 = plt.subplots(figsize=(12, 10))

    # Aggregate data at gene level
    # For each gene pair, take the maximum IPR domain length across all transcripts
    # This represents the most complete isoform
    df_gene_level = df.groupby(['ref_gene', 'query_gene']).agg({
        'query_total_ipr_domain_length': 'max',
        'ref_total_ipr_domain_length': 'max',
        'class_type': 'first'  # Take first class_type for the gene pair
    }).reset_index()

    print(f"\nGene-level aggregation: {len(df)} transcript pairs → {len(df_gene_level)} gene pairs", file=sys.stderr)

    # Define quadrants based on presence/absence at gene level
    df_plot = df_gene_level.copy()

    # Default: both present
    df_plot['quadrant'] = 'Present in both'

    # Absent in both (NA in both)
    df_plot.loc[df_plot['query_total_ipr_domain_length'].isna() &
                df_plot['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Absent in both'

    # Ref only (query is NA, ref has value > 0)
    df_plot.loc[df_plot['query_total_ipr_domain_length'].isna() &
                (df_plot['ref_total_ipr_domain_length'] > 0), 'quadrant'] = 'Ref only'

    # Query only (query has value > 0, ref is NA)
    df_plot.loc[(df_plot['query_total_ipr_domain_length'] > 0) &
                df_plot['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Query only'

    # Calculate unique gene counts for each quadrant
    print(f"\nGene-level quadrant distribution (unique gene counts):", file=sys.stderr)
    for quad in ['Present in both', 'Absent in both', 'Ref only', 'Query only']:
        subset = df_plot[df_plot['quadrant'] == quad]
        unique_ref = subset['ref_gene'].nunique()
        unique_query = subset['query_gene'].nunique()
        total_unique = unique_ref + unique_query
        print(f"  {quad}:", file=sys.stderr)
        print(f"    - Unique {ref_genome_prefix} genes: {unique_ref}", file=sys.stderr)
        print(f"    - Unique {qry_genome_prefix} genes: {unique_query}", file=sys.stderr)
        print(f"    - Total unique genes: {total_unique}", file=sys.stderr)

    quadrant_colors = {
        'Present in both': 'green',
        'Absent in both': 'gray',
        'Ref only': 'red',
        'Query only': 'blue'
    }

    # Calculate unique gene counts for legend labels
    quadrant_labels = {}
    for quad in quadrant_colors.keys():
        subset = df_plot[df_plot['quadrant'] == quad]
        unique_ref = subset['ref_gene'].nunique()
        unique_query = subset['query_gene'].nunique()
        total_unique_genes = unique_ref + unique_query
        quadrant_labels[quad] = f"{quad}\n(genes: {total_unique_genes}, pairs: {len(subset)})"

    for quad, color in quadrant_colors.items():
        subset = df_plot[df_plot['quadrant'] == quad]
        # Add small jitter to zeros for visibility
        x = subset['query_total_ipr_domain_length'].copy()
        y = subset['ref_total_ipr_domain_length'].copy()

        if quad == 'Absent in both':
            # Jitter for both absent
            x = np.random.normal(0, 5, len(subset))
            y = np.random.normal(0, 5, len(subset))
        elif quad == 'Ref only':
            # Jitter for query=0
            x = np.random.normal(0, 5, len(subset))
        elif quad == 'Query only':
            # Jitter for ref=0
            y = np.random.normal(0, 5, len(subset))

        ax2.scatter(x, y,
                  c=color,
                  label=quadrant_labels[quad],
                  alpha=0.5,
                  s=40,
                  edgecolors='black',
                  linewidth=0.2)

    max_val = max(df_gene_level['query_total_ipr_domain_length'].max(),
                  df_gene_level['ref_total_ipr_domain_length'].max())
    ax2.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2, label='y=x')

    if ref_genome_prefix:
        ax2.set_xlabel(f'{qry_genome_prefix} Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')
        ax2.set_ylabel(f'{ref_genome_prefix} Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')
    else:
        ax2.set_xlabel('Query Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Reference Total IPR Domain Length (aa)', fontsize=14, fontweight='bold')

    ax2.set_title('Gene-level Presence/Absence Patterns of IPR Domains', fontsize=16, fontweight='bold')

    ax2.legend(fontsize=14)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f"{output_prefix}_quadrants_gene_level.png", bbox_inches='tight')
    print(f"Saved: {output_prefix}_quadrants_gene_level.png", file=sys.stderr)
    plt.close()


def analyze_inconsistent_genes(df, output_prefix, ref_genome_prefix, qry_genome_prefix):
    """Identify and export genes with transcripts in different quadrant categories"""

    # Assign quadrants to all transcript pairs
    df_analysis = df.copy()
    df_analysis['quadrant'] = 'Present in both'

    df_analysis.loc[df_analysis['query_total_ipr_domain_length'].isna() &
                    df_analysis['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Absent in both'

    df_analysis.loc[df_analysis['query_total_ipr_domain_length'].isna() &
                    (df_analysis['ref_total_ipr_domain_length'] > 0), 'quadrant'] = 'Ref only'

    df_analysis.loc[(df_analysis['query_total_ipr_domain_length'] > 0) &
                    df_analysis['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Query only'

    # Find gene pairs with multiple quadrants
    gene_pair_quadrants = df_analysis.groupby(['ref_gene', 'query_gene'])['quadrant'].apply(
        lambda x: list(x.unique())
    ).reset_index()
    gene_pair_quadrants['num_quadrants'] = gene_pair_quadrants['quadrant'].apply(len)

    # Filter to only those with multiple quadrants
    inconsistent_gene_pairs = gene_pair_quadrants[gene_pair_quadrants['num_quadrants'] > 1]

    if len(inconsistent_gene_pairs) == 0:
        print("\nNo genes with transcripts in multiple quadrants found.", file=sys.stderr)
        return

    print(f"\n{'='*80}", file=sys.stderr)
    print(f"GENES WITH TRANSCRIPTS IN MULTIPLE QUADRANTS", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Found {len(inconsistent_gene_pairs)} gene pairs with inconsistent quadrant assignments", file=sys.stderr)

    # Get detailed information for these genes - keep ALL original columns
    inconsistent_details = []
    for _, row in inconsistent_gene_pairs.iterrows():
        ref_g = row['ref_gene']
        qry_g = row['query_gene']
        # Get data from original df to preserve all columns, then add quadrant
        subset_original = df[(df['ref_gene'] == ref_g) & (df['query_gene'] == qry_g)].copy()

        # Add quadrant assignments
        subset_original['quadrant'] = 'Present in both'
        subset_original.loc[subset_original['query_total_ipr_domain_length'].isna() &
                           subset_original['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Absent in both'
        subset_original.loc[subset_original['query_total_ipr_domain_length'].isna() &
                           (subset_original['ref_total_ipr_domain_length'] > 0), 'quadrant'] = 'Ref only'
        subset_original.loc[(subset_original['query_total_ipr_domain_length'] > 0) &
                           subset_original['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Query only'

        inconsistent_details.append(subset_original)

    df_inconsistent = pd.concat(inconsistent_details, ignore_index=True)

    # Sort by gene pairs and quadrant for easier reading
    df_inconsistent = df_inconsistent.sort_values(['ref_gene', 'query_gene', 'quadrant'])

    # Export to TSV with ALL original columns
    output_file = f"{output_prefix}_inconsistent_genes.tsv"
    df_inconsistent.to_csv(output_file, sep='\t', index=False)
    print(f"Exported detailed data (all columns) to: {output_file}", file=sys.stderr)

    # Create summary by quadrant combinations
    summary_data = []
    for _, row in inconsistent_gene_pairs.iterrows():
        ref_g = row['ref_gene']
        qry_g = row['query_gene']
        quadrants = sorted(row['quadrant'])

        subset = df_analysis[(df_analysis['ref_gene'] == ref_g) &
                            (df_analysis['query_gene'] == qry_g)]

        quadrant_counts = subset['quadrant'].value_counts().to_dict()

        summary_data.append({
            'ref_gene': ref_g,
            'query_gene': qry_g,
            'num_transcripts': len(subset),
            'quadrants': ', '.join(quadrants),
            **{f'count_{q.replace(" ", "_")}': quadrant_counts.get(q, 0)
               for q in ['Present in both', 'Absent in both', 'Ref only', 'Query only']}
        })

    df_summary = pd.DataFrame(summary_data)
    summary_file = f"{output_prefix}_inconsistent_genes_summary.tsv"
    df_summary.to_csv(summary_file, sep='\t', index=False)
    print(f"Exported summary to: {summary_file}", file=sys.stderr)

    # Print statistics
    print(f"\nQuadrant combination statistics:", file=sys.stderr)
    quadrant_combo_counts = df_summary['quadrants'].value_counts()
    for combo, count in quadrant_combo_counts.items():
        print(f"  {combo}: {count} gene pairs", file=sys.stderr)

    # Identify unique genes involved
    unique_ref_genes = df_inconsistent['ref_gene'].nunique()
    unique_qry_genes = df_inconsistent['query_gene'].nunique()
    print(f"\nUnique genes with inconsistent transcripts:", file=sys.stderr)
    print(f"  {ref_genome_prefix} genes: {unique_ref_genes}", file=sys.stderr)
    print(f"  {qry_genome_prefix} genes: {unique_qry_genes}", file=sys.stderr)
    print(f"  Total: {unique_ref_genes + unique_qry_genes}", file=sys.stderr)

    # Create visualization
    plot_inconsistent_genes(df_summary, output_prefix, ref_genome_prefix, qry_genome_prefix)

    return df_inconsistent, df_summary


def plot_inconsistent_genes(df_summary, output_prefix, ref_genome_prefix, qry_genome_prefix):
    """Create informative plot for genes with transcripts in multiple quadrants"""

    if df_summary is None or len(df_summary) == 0:
        return

    # Create figure with 3 subplots
    fig = plt.figure(figsize=(22, 8))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1, 1.2])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    ax3 = fig.add_subplot(gs[2])

    # Plot 1: Bar chart of quadrant combinations
    quadrant_combo_counts = df_summary['quadrants'].value_counts().sort_values(ascending=True)

    colors_map = {
        'Absent in both, Present in both': '#FFA500',  # Orange
        'Present in both, Ref only': '#FF6B6B',  # Light red
        'Present in both, Query only': '#4ECDC4',  # Teal
        'Absent in both, Ref only': '#95E1D3',  # Mint
        'Absent in both, Query only': '#F38181',  # Salmon
        'Absent in both, Present in both, Ref only': '#9B59B6',  # Purple
        'Absent in both, Present in both, Query only': '#E67E22',  # Dark orange
    }

    bar_colors = [colors_map.get(combo, '#CCCCCC') for combo in quadrant_combo_counts.index]

    ax1.barh(range(len(quadrant_combo_counts)), quadrant_combo_counts.values, color=bar_colors, edgecolor='black', linewidth=1)
    ax1.set_yticks(range(len(quadrant_combo_counts)))
    ax1.set_yticklabels(quadrant_combo_counts.index, fontsize=10)
    ax1.set_xlabel('Number of Gene Pairs', fontsize=12, fontweight='bold')
    ax1.set_title('Quadrant Combination\nDistribution',
                  fontsize=13, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)

    # Add value labels on bars
    for i, v in enumerate(quadrant_combo_counts.values):
        ax1.text(v + 0.5, i, str(v), va='center', fontsize=9, fontweight='bold')

    # Plot 2: Stacked bar chart showing quadrant distribution
    quadrant_cols = ['count_Present_in_both', 'count_Absent_in_both', 'count_Ref_only', 'count_Query_only']
    quadrant_labels = ['Present\nin both', 'Absent\nin both', 'Ref\nonly', 'Query\nonly']
    quadrant_colors = ['green', 'gray', 'red', 'blue']

    # Sum up the counts for each quadrant
    quadrant_totals = [df_summary[col].sum() for col in quadrant_cols]

    ax2.bar(quadrant_labels, quadrant_totals, color=quadrant_colors, edgecolor='black', linewidth=1, alpha=0.7)
    ax2.set_ylabel('Total Transcripts', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Quadrant', fontsize=12, fontweight='bold')
    ax2.set_title('Transcript Distribution\nAcross Quadrants',
                  fontsize=13, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for i, (label, value) in enumerate(zip(quadrant_labels, quadrant_totals)):
        if value > 0:
            ax2.text(i, value + max(quadrant_totals) * 0.02, str(value),
                    ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Plot 3: Top gene pairs with most transcripts or most diverse quadrants
    # Sort by number of transcripts descending
    top_gene_pairs = df_summary.nlargest(min(15, len(df_summary)), 'num_transcripts')

    # Create labels for gene pairs (abbreviated)
    gene_pair_labels = []
    for _, row in top_gene_pairs.iterrows():
        ref_short = row['ref_gene'].split('-')[-1].split('_')[0][-8:]  # Last 8 chars of gene ID
        qry_short = row['query_gene'].split('_')[0][-8:]  # Last 8 chars of gene ID
        gene_pair_labels.append(f"{ref_short}\nvs\n{qry_short}")

    # Create stacked bar chart for each gene pair
    x_pos = np.arange(len(top_gene_pairs))
    bar_width = 0.8

    bottom = np.zeros(len(top_gene_pairs))
    for idx, (col, label, color) in enumerate(zip(quadrant_cols, ['Present', 'Absent', 'Ref only', 'Qry only'], quadrant_colors)):
        values = top_gene_pairs[col].values
        ax3.bar(x_pos, values, bar_width, label=label, color=color, bottom=bottom, edgecolor='black', linewidth=0.5, alpha=0.8)
        bottom += values

    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(gene_pair_labels, fontsize=8, rotation=0)
    ax3.set_ylabel('Number of Transcripts', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Gene Pairs (Top by Transcript Count)', fontsize=12, fontweight='bold')
    ax3.set_title(f'Quadrant Distribution\nfor Top {len(top_gene_pairs)} Gene Pairs',
                  fontsize=13, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_file = f"{output_prefix}_inconsistent_genes_summary_plot.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"Saved inconsistent genes summary plot: {output_file}", file=sys.stderr)
    plt.close()


def extract_genome_prefix(gene_name):
    """Extract genome prefix from gene name"""
    # Handle different gene name formats
    # e.g., "gene-FOBCDRAFT_150845" -> "FOBCDRAFT"
    # e.g., "FOZG_17472" -> "FOZG"

    if pd.isna(gene_name):
        return None

    gene_str = str(gene_name)

    # Remove "gene-" prefix if present
    if gene_str.startswith('gene-'):
        gene_str = gene_str[5:]

    # Split by underscore and take first part
    if '_' in gene_str:
        return gene_str.split('_')[0]

    # Split by hyphen and take first part
    if '-' in gene_str:
        return gene_str.split('-')[0]

    return gene_str


def auto_detect_prefixes(df):
    """Automatically detect reference and query genome prefixes from data"""
    # Get the most common prefix for reference genes
    ref_prefixes = df['ref_gene'].dropna().apply(extract_genome_prefix).value_counts()
    query_prefixes = df['query_gene'].dropna().apply(extract_genome_prefix).value_counts()

    if len(ref_prefixes) == 0 or len(query_prefixes) == 0:
        return "Reference", "Query"

    ref_prefix = ref_prefixes.index[0]
    query_prefix = query_prefixes.index[0]

    print(f"Auto-detected prefixes: Reference='{ref_prefix}', Query='{query_prefix}'", file=sys.stderr)

    return ref_prefix, query_prefix


def print_summary_stats(df, ref_genome_prefix, qry_genome_prefix):
    """Print comprehensive summary statistics"""
    print("\n" + "="*80, file=sys.stderr)
    print("COMPREHENSIVE SUMMARY STATISTICS", file=sys.stderr)
    print("="*80, file=sys.stderr)

    # ===== Overall Data Summary =====
    print(f"\n{'─'*80}", file=sys.stderr)
    print("OVERALL DATA", file=sys.stderr)
    print(f"{'─'*80}", file=sys.stderr)

    total_transcripts = len(df)
    unique_ref_genes = df['ref_gene'].nunique()
    unique_qry_genes = df['query_gene'].nunique()
    unique_gene_pairs = df[['ref_gene', 'query_gene']].drop_duplicates().shape[0]

    print(f"Total transcript pairs: {total_transcripts:,}", file=sys.stderr)
    print(f"Unique {ref_genome_prefix} genes: {unique_ref_genes:,}", file=sys.stderr)
    print(f"Unique {qry_genome_prefix} genes: {unique_qry_genes:,}", file=sys.stderr)
    print(f"Unique gene pairs: {unique_gene_pairs:,}", file=sys.stderr)
    print(f"Average transcripts per gene pair: {total_transcripts/unique_gene_pairs:.2f}", file=sys.stderr)

    # ===== Transcript-Level Statistics =====
    print(f"\n{'─'*80}", file=sys.stderr)
    print("TRANSCRIPT-LEVEL PRESENCE/ABSENCE", file=sys.stderr)
    print(f"{'─'*80}", file=sys.stderr)

    # Assign quadrants for transcript level
    df_transcript = df.copy()
    df_transcript['quadrant'] = 'Present in both'
    df_transcript.loc[df_transcript['query_total_ipr_domain_length'].isna() &
                      df_transcript['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Absent in both'
    df_transcript.loc[df_transcript['query_total_ipr_domain_length'].isna() &
                      (df_transcript['ref_total_ipr_domain_length'] > 0), 'quadrant'] = 'Ref only'
    df_transcript.loc[(df_transcript['query_total_ipr_domain_length'] > 0) &
                      df_transcript['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Query only'

    transcript_quad_counts = df_transcript['quadrant'].value_counts()
    for quadrant in ['Present in both', 'Absent in both', 'Ref only', 'Query only']:
        count = transcript_quad_counts.get(quadrant, 0)
        pct = 100 * count / total_transcripts if total_transcripts > 0 else 0
        print(f"  {quadrant:20s}: {count:6,} ({pct:5.1f}%)", file=sys.stderr)

    # ===== Gene-Level Statistics =====
    print(f"\n{'─'*80}", file=sys.stderr)
    print("GENE-LEVEL PRESENCE/ABSENCE (Unique Genes)", file=sys.stderr)
    print(f"{'─'*80}", file=sys.stderr)

    # Aggregate at gene level
    df_gene_level = df.groupby(['ref_gene', 'query_gene']).agg({
        'query_total_ipr_domain_length': 'max',
        'ref_total_ipr_domain_length': 'max'
    }).reset_index()

    df_gene_level['quadrant'] = 'Present in both'
    df_gene_level.loc[df_gene_level['query_total_ipr_domain_length'].isna() &
                      df_gene_level['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Absent in both'
    df_gene_level.loc[df_gene_level['query_total_ipr_domain_length'].isna() &
                      (df_gene_level['ref_total_ipr_domain_length'] > 0), 'quadrant'] = 'Ref only'
    df_gene_level.loc[(df_gene_level['query_total_ipr_domain_length'] > 0) &
                      df_gene_level['ref_total_ipr_domain_length'].isna(), 'quadrant'] = 'Query only'

    for quadrant in ['Present in both', 'Absent in both', 'Ref only', 'Query only']:
        subset = df_gene_level[df_gene_level['quadrant'] == quadrant]
        unique_ref = subset['ref_gene'].nunique()
        unique_qry = subset['query_gene'].nunique()
        total_unique = unique_ref + unique_qry

        print(f"  {quadrant}:", file=sys.stderr)
        print(f"    - {ref_genome_prefix} genes: {unique_ref:,}", file=sys.stderr)
        print(f"    - {qry_genome_prefix} genes: {unique_qry:,}", file=sys.stderr)
        print(f"    - Total unique genes: {total_unique:,}", file=sys.stderr)

    # ===== IPR Domain Length Statistics =====
    both_present = df_transcript[df_transcript['quadrant'] == 'Present in both']
    if len(both_present) > 0:
        print(f"\n{'─'*80}", file=sys.stderr)
        print("IPR DOMAIN LENGTH STATISTICS (Present in both)", file=sys.stderr)
        print(f"{'─'*80}", file=sys.stderr)

        corr = both_present['query_total_ipr_domain_length'].corr(
            both_present['ref_total_ipr_domain_length'])

        print(f"  Number of transcript pairs: {len(both_present):,}", file=sys.stderr)
        print(f"  Pearson correlation: {corr:.4f}", file=sys.stderr)
        print(f"\n  {qry_genome_prefix} IPR domain lengths:", file=sys.stderr)
        print(f"    - Mean: {both_present['query_total_ipr_domain_length'].mean():.1f} aa", file=sys.stderr)
        print(f"    - Median: {both_present['query_total_ipr_domain_length'].median():.1f} aa", file=sys.stderr)
        print(f"    - Range: {both_present['query_total_ipr_domain_length'].min():.0f} - {both_present['query_total_ipr_domain_length'].max():.0f} aa", file=sys.stderr)

        print(f"\n  {ref_genome_prefix} IPR domain lengths:", file=sys.stderr)
        print(f"    - Mean: {both_present['ref_total_ipr_domain_length'].mean():.1f} aa", file=sys.stderr)
        print(f"    - Median: {both_present['ref_total_ipr_domain_length'].median():.1f} aa", file=sys.stderr)
        print(f"    - Range: {both_present['ref_total_ipr_domain_length'].min():.0f} - {both_present['ref_total_ipr_domain_length'].max():.0f} aa", file=sys.stderr)

        ratio = both_present['query_total_ipr_domain_length'] / both_present['ref_total_ipr_domain_length']
        print(f"\n  {qry_genome_prefix}/{ref_genome_prefix} ratio:", file=sys.stderr)
        print(f"    - Mean: {ratio.mean():.3f}", file=sys.stderr)
        print(f"    - Median: {ratio.median():.3f}", file=sys.stderr)

    # ===== Class Type Distribution =====
    print(f"\n{'─'*80}", file=sys.stderr)
    print("GFFCOMPARE CLASS TYPE DISTRIBUTION", file=sys.stderr)
    print(f"{'─'*80}", file=sys.stderr)

    class_type_counts = df['class_type'].value_counts().head(10)
    for class_type, count in class_type_counts.items():
        pct = 100 * count / total_transcripts
        print(f"  {class_type:15s}: {count:6,} ({pct:5.1f}%)", file=sys.stderr)

    if len(df['class_type'].value_counts()) > 10:
        print(f"  ... and {len(df['class_type'].value_counts()) - 10} more", file=sys.stderr)

    print("\n" + "="*80 + "\n", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Plot query vs reference total IPR domain lengths from PAVprot output"
    )
    parser.add_argument('input', help="PAVprot output TSV file")
    parser.add_argument('--output-prefix', '-o', default='ipr_comparison',
                       help="Output prefix for plot files (default: ipr_comparison)")
    parser.add_argument('--ref-qry-prefix', default=None,
                       help="Comma or space-separated reference and query genome prefixes. If not provided, will auto-detect from data.")


    args = parser.parse_args()

    # Load data
    print(f"\nLoading data from: {args.input}", file=sys.stderr)
    df = load_pavprot_data(args.input)
    print(f"Loaded {len(df)} entries", file=sys.stderr)

    # Parse ref-qry-prefix
    if args.ref_qry_prefix:
        # Split by comma first, then by space if no comma found
        if ',' in args.ref_qry_prefix:
            prefixes = [p.strip() for p in args.ref_qry_prefix.split(',')]
        else:
            prefixes = args.ref_qry_prefix.split()

        if len(prefixes) != 2:
            print(f"Error: --ref-qry-prefix must contain exactly 2 values (ref,query), got {len(prefixes)}", file=sys.stderr)
            sys.exit(1)

        ref_genome_prefix = prefixes[0]
        qry_genome_prefix = prefixes[1]
        print(f"Using provided prefixes: Reference='{ref_genome_prefix}', Query='{qry_genome_prefix}'", file=sys.stderr)
    else:
        # Auto-detect prefixes from data
        ref_genome_prefix, qry_genome_prefix = auto_detect_prefixes(df)

    # Print comprehensive summary statistics
    print_summary_stats(df, ref_genome_prefix, qry_genome_prefix)

    # Create output directory if needed
    output_path = Path(args.output_prefix)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate plots
    print("\nGenerating plots...", file=sys.stderr)
    plot_scatter_by_class_type(df, args.output_prefix, ref_genome_prefix, qry_genome_prefix)
    plot_density_hexbin(df, args.output_prefix, ref_genome_prefix, qry_genome_prefix)
    plot_log_scale(df, args.output_prefix, ref_genome_prefix, qry_genome_prefix)
    # plot_ratio_distribution(df, args.output_prefix)
    plot_four_quadrants(df, args.output_prefix, ref_genome_prefix, qry_genome_prefix)
    plot_four_quadrants_gene_level(df, args.output_prefix, ref_genome_prefix, qry_genome_prefix)

    print("\n✓ All plots generated successfully!", file=sys.stderr)

    # Analyze genes with transcripts in multiple quadrants
    analyze_inconsistent_genes(df, args.output_prefix, ref_genome_prefix, qry_genome_prefix)

if __name__ == '__main__':
    main()
