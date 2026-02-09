#!/usr/bin/env python3
"""
Task 8 Fungidb Analysis

Extracted from: task_8_fungidb_analysis
Moved to plot module for production use.
"""

from pathlib import Path
from typing import Optional
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def mapping_type_to_colon(mapping_type: str) -> str:
    """Convert mapping_type to colon notation (e.g., '1to1' -> '1:1')."""
    return mapping_type.replace('to', ':')


def generate_fungidb_analysis(gene_df: pd.DataFrame = None, transcript_df: pd.DataFrame = None, output_dir: Path = None, config: dict = None, figure_dpi: int = 150) -> Optional[Path]:
    """
    Analyze transcript counts across FungiDB phytopathogens.

    Generates:
    - Summary tables at genus and order level
    - Visualization plots (transcripts per gene, exon distributions)

    Returns:
        Path to output directory, or None if skipped
    """
    print("\n[Task 8] FungiDB Transcript Analysis")

    phyto_file = Path(config["phytopathogen_list"])
    stats_file = Path(config["fungidb_gene_stats"])

    if not check_file_exists(phyto_file, "Phytopathogen list"):
        return None
    if not check_file_exists(stats_file, "FungiDB gene stats"):
        return None

    # Load data
    print(f"  Loading phytopathogen list: {phyto_file}")
    phyto_df = pd.read_csv(phyto_file)

    print(f"  Loading gene stats: {stats_file}")
    stats_df = pd.read_csv(stats_file, sep='\t', low_memory=False)
    print(f"    Loaded {len(stats_df)} gene records")

    # Handle comma-separated exon_counts (multi-transcript genes)
    # Take mean of exon counts for multi-transcript genes
    def parse_exon_counts(x):
        if pd.isna(x):
            return np.nan
        if isinstance(x, (int, float)):
            return float(x)
        # Handle comma-separated values
        try:
            vals = [float(v.strip()) for v in str(x).split(',')]
            return np.mean(vals)
        except:
            return np.nan

    stats_df['exon_counts_numeric'] = stats_df['exon_counts'].apply(parse_exon_counts)

    # Ensure transcripts_per_gene is numeric
    stats_df['transcripts_per_gene'] = pd.to_numeric(stats_df['transcripts_per_gene'], errors='coerce')

    # Extract genus from organism column in phytopathogen list
    # The format is <i>Genus</i> or <i>Genus species</i>
    def extract_genus(org_str):
        import re
        # Remove HTML tags and extract first word (genus)
        clean = re.sub(r'<[^>]+>', '', str(org_str)).strip()
        return clean.split()[0] if clean else None

    phyto_df['genus_extracted'] = phyto_df['Organism'].apply(extract_genus)

    # Filter to significant plant pathogens
    plant_pathogen_col = 'Significant Plant Pathogen'
    if plant_pathogen_col in phyto_df.columns:
        phyto_fungi = phyto_df[
            (phyto_df[plant_pathogen_col].fillna('').str.lower() == 'yes') &
            (phyto_df['VEuPathDB Database'].fillna('').str.lower() == 'fungidb')
        ]
        print(f"  Found {len(phyto_fungi)} significant plant pathogens in FungiDB")
    else:
        print(f"  [WARN] Column '{plant_pathogen_col}' not found")
        phyto_fungi = phyto_df

    if len(phyto_fungi) == 0:
        print("  [SKIP] No FungiDB plant pathogens found")
        return None

    # Get list of phytopathogen genera
    phyto_genera = set(phyto_fungi['genus_extracted'].dropna().unique())
    print(f"  Phytopathogen genera: {sorted(phyto_genera)}")

    # Filter gene stats to phytopathogen genera
    filtered_stats = stats_df[stats_df['genus'].isin(phyto_genera)]
    print(f"  Matched {len(filtered_stats)} genes from phytopathogen genera")

    if len(filtered_stats) == 0:
        print("  [SKIP] No matching genes found")
        return None

    # Create output subdirectory for Task 8
    task8_dir = output_dir / "fungidb_analysis"
    task8_dir.mkdir(exist_ok=True)

    # ===== Summary by Genus =====
    genus_summary = filtered_stats.groupby('genus').agg({
        'gene_id': 'count',
        'transcripts_per_gene': ['mean', 'median', 'std'],
        'exon_counts_numeric': ['mean','std'],
        'organism_abbreviation': 'nunique'
    }).round(3)
    genus_summary.columns = ['gene_count', 'mean_transcripts', 'median_transcripts',
                             'std_transcripts', 'mean_exons', 'std_exons', 'num_organisms']
    genus_summary['mean_genes_per_organism'] = (genus_summary['gene_count'] / genus_summary['num_organisms']).round(0).astype(int)
    genus_summary = genus_summary.sort_values('gene_count', ascending=False)

    genus_file = task8_dir / "summary_by_genus.tsv"
    genus_summary.to_csv(genus_file, sep='\t')
    print(f"  [DONE] Saved: {genus_file}")

    # ===== Summary by Order =====
    order_summary = filtered_stats.groupby('order').agg({
        'gene_id': 'count',
        'transcripts_per_gene': ['mean', 'median', 'std'],
        'exon_counts_numeric': ['mean','std'],
        'genus': 'nunique',
        'organism_abbreviation': 'nunique'
    }).round(3)
    order_summary.columns = ['gene_count', 'mean_transcripts', 'median_transcripts',
                            'std_transcripts', 'mean_exons', 'std_exons', 'num_genera', 'num_organisms']
    order_summary = order_summary.sort_values('gene_count', ascending=False)

    order_file = task8_dir / "summary_by_order.tsv"
    order_summary.to_csv(order_file, sep='\t')
    print(f"  [DONE] Saved: {order_file}")

    # ===== Full filtered dataset =====
    filtered_file = task8_dir / "phytopathogen_gene_stats.tsv"
    filtered_stats.to_csv(filtered_file, sep='\t', index=False)
    print(f"  [DONE] Saved: {filtered_file}")

    # ===== Visualization Plots =====
    # Plot 1: Transcripts per gene by genus
    fig1, ax1 = plt.subplots(figsize=(14, 6))

    # Get top genera by gene count
    top_genera = genus_summary.head(15).index.tolist()
    plot_data = filtered_stats[filtered_stats['genus'].isin(top_genera)].copy()

    genus_order = [g for g in genus_summary.index if g in top_genera]
    plot_data['genus'] = pd.Categorical(plot_data['genus'], categories=genus_order, ordered=True)

    # Box plot
    plot_data.boxplot(column='transcripts_per_gene', by='genus', ax=ax1)
    ax1.set_xlabel('Genus')
    ax1.set_ylabel('Transcripts per Gene')
    ax1.set_title('Transcripts per Gene by Genus (Top 15 Phytopathogen Genera)')
    plt.suptitle('')  # Remove default title
    ax1.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plot1_path = task8_dir / "transcripts_by_genus.png"
    fig1.savefig(plot1_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig1)
    print(f"  [DONE] Saved: {plot1_path}")

    # Plot 2a: Exon counts PER GENE by order (mean of transcript exon counts)
    fig2a, ax2a = plt.subplots(figsize=(12, 6))

    top_orders = order_summary.head(10).index.tolist()
    order_data = filtered_stats[filtered_stats['order'].isin(top_orders)].copy()

    order_order = [o for o in order_summary.index if o in top_orders]
    order_data['order'] = pd.Categorical(order_data['order'], categories=order_order, ordered=True)

    order_data.boxplot(column='exon_counts_numeric', by='order', ax=ax2a)
    ax2a.set_xlabel('Order')
    ax2a.set_ylabel('Mean Exon Count per Gene')
    ax2a.set_title('Exon Counts per Gene by Order (Top 10 Phytopathogen Orders)')
    plt.suptitle('')
    ax2a.tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plot2a_path = task8_dir / "exons_per_gene_by_order.png"
    fig2a.savefig(plot2a_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig2a)
    print(f"  [DONE] Saved: {plot2a_path}")

    # Plot 2b: Exon counts PER TRANSCRIPT by order (expand comma-separated values)
    # Expand comma-separated exon counts to get individual transcript values
    def expand_exon_counts(df):
        rows = []
        for _, row in df.iterrows():
            exon_str = row['exon_counts']
            order_val = row['order']
            if pd.isna(exon_str):
                continue
            # Handle comma-separated values
            if isinstance(exon_str, str) and ',' in exon_str:
                for val in exon_str.split(','):
                    try:
                        rows.append({'order': order_val, 'exon_count': float(val.strip())})
                    except:
                        pass
            else:
                try:
                    rows.append({'order': order_val, 'exon_count': float(exon_str)})
                except:
                    pass
        return pd.DataFrame(rows)

    # Only expand for top orders to avoid memory issues
    order_subset = filtered_stats[filtered_stats['order'].isin(top_orders)][['order', 'exon_counts']]
    expanded_exons = expand_exon_counts(order_subset)

    if len(expanded_exons) > 0:
        fig2b, ax2b = plt.subplots(figsize=(12, 6))

        expanded_exons['order'] = pd.Categorical(expanded_exons['order'], categories=order_order, ordered=True)
        expanded_exons.boxplot(column='exon_count', by='order', ax=ax2b)
        ax2b.set_xlabel('Order')
        ax2b.set_ylabel('Exon Count per Transcript')
        ax2b.set_title('Exon Counts per Transcript by Order (Top 10 Phytopathogen Orders)')
        plt.suptitle('')
        ax2b.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plot2b_path = task8_dir / "exons_per_transcript_by_order.png"
        fig2b.savefig(plot2b_path, dpi=figure_dpi, bbox_inches='tight')
        plt.close(fig2b)
        print(f"  [DONE] Saved: {plot2b_path}")

    # Plot 3: Bar chart - gene counts by genus
    fig3, ax3 = plt.subplots(figsize=(12, 6))

    genus_counts = genus_summary['gene_count'].head(15)
    colors = plt.cm.viridis(np.linspace(0, 0.8, len(genus_counts)))
    bars = ax3.barh(genus_counts.index[::-1], genus_counts.values[::-1], color=colors[::-1])

    ax3.set_xlabel('Number of Genes')
    ax3.set_ylabel('Genus')
    ax3.set_title('Gene Counts by Phytopathogen Genus (Top 15)')

    # Add count labels
    for bar in bars:
        width = bar.get_width()
        ax3.text(width + max(genus_counts)*0.01, bar.get_y() + bar.get_height()/2,
                f'{int(width):,}', va='center', fontsize=8)

    plt.tight_layout()
    plot3_path = task8_dir / "gene_counts_by_genus.png"
    fig3.savefig(plot3_path, dpi=figure_dpi, bbox_inches='tight')
    plt.close(fig3)
    print(f"  [DONE] Saved: {plot3_path}")

    # Print summary
    print(f"\n  Summary:")
    print(f"    Total phytopathogen genera: {len(phyto_genera)}")
    print(f"    Matched genera in FungiDB: {filtered_stats['genus'].nunique()}")
    print(f"    Total genes analyzed: {len(filtered_stats):,}")
    print(f"    Output directory: {task8_dir}")

    return task8_dir



if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        gene_file = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else Path.cwd()
        gene_df = pd.read_csv(gene_file, sep='\t')
        print(f"Generating plot from {gene_file}")
        print(f"Output to {out_dir}")
