#!/usr/bin/env python3
"""
FungiDB Species-level Analysis: Transcript per gene and exon count per gene.

Generates summary tables for:
1. Phytopathogen species
2. All FungiDB species

Usage:
    python analyze_fungidb_species.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Configuration
PHYTO_LIST = Path("/Users/sadik/Documents/projects/data/disease_research_supported.csv")
GENE_STATS = Path("/Users/sadik/Documents/projects/data/fungidb_v68_gene_stats.tsv")
OUTPUT_DIR = Path("pipeline_output/fungidb_analysis")


def parse_exon_counts(exon_str):
    """Parse comma-separated exon counts and return mean."""
    if pd.isna(exon_str):
        return np.nan
    try:
        if isinstance(exon_str, (int, float)):
            return float(exon_str)
        values = [float(x.strip()) for x in str(exon_str).split(',') if x.strip()]
        return np.mean(values) if values else np.nan
    except:
        return np.nan


def main():
    print("Loading data...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load phytopathogen list
    phyto_df = pd.read_csv(PHYTO_LIST)
    # Extract genus from Organism column (remove HTML tags, then take first word)
    phyto_df['organism_clean'] = phyto_df['Organism'].str.replace(r'<[^>]+>', '', regex=True).str.strip()
    phyto_df['genus_clean'] = phyto_df['organism_clean'].str.split().str[0]
    phyto_genera = phyto_df[phyto_df['Significant Plant Pathogen'] == 'Yes']['genus_clean'].unique().tolist()
    print(f"  Phytopathogen genera: {len(phyto_genera)}")
    print(f"    Genera: {sorted(phyto_genera)}")

    # Load gene stats
    print(f"  Loading FungiDB gene stats...")
    gene_df = pd.read_csv(GENE_STATS, sep='\t', low_memory=False)
    print(f"    Total genes: {len(gene_df):,}")

    # Parse exon counts
    gene_df['exon_mean'] = gene_df['exon_counts'].apply(parse_exon_counts)

    # Species column already contains full species name (e.g., "Aspergillus aculeatus")

    # Rename transcripts column if needed
    if 'transcripts_per_gene' in gene_df.columns:
        gene_df['transcript_count'] = gene_df['transcripts_per_gene']
    elif 'transcripts' in gene_df.columns:
        gene_df['transcript_count'] = gene_df['transcripts']

    # ===== Species-level summary for ALL FungiDB =====
    print("\nGenerating all FungiDB species summary...")
    all_species = gene_df.groupby(['species', 'genus']).agg({
        'gene_id': 'count',
        'transcript_count': ['mean', 'median', 'std'],
        'exon_mean': ['mean', 'median', 'std']
    }).reset_index()

    # Flatten column names
    all_species.columns = ['species', 'genus', 'gene_count',
                           'mean_transcripts', 'median_transcripts', 'std_transcripts',
                           'mean_exons', 'median_exons', 'std_exons']

    # Round values
    for col in ['mean_transcripts', 'median_transcripts', 'std_transcripts',
                'mean_exons', 'median_exons', 'std_exons']:
        all_species[col] = all_species[col].round(3)

    # Sort by gene count
    all_species = all_species.sort_values('gene_count', ascending=False)

    all_species_path = OUTPUT_DIR / "summary_by_species_all.tsv"
    all_species.to_csv(all_species_path, sep='\t', index=False)
    print(f"  [DONE] Saved: {all_species_path}")
    print(f"    Total species: {len(all_species)}")

    # ===== Species-level summary for PHYTOPATHOGENS =====
    print("\nGenerating phytopathogen species summary...")
    phyto_genes = gene_df[gene_df['genus'].isin(phyto_genera)]
    print(f"    Matched phytopathogen genes: {len(phyto_genes):,}")

    phyto_species = phyto_genes.groupby(['species', 'genus']).agg({
        'gene_id': 'count',
        'transcript_count': ['mean', 'median', 'std'],
        'exon_mean': ['mean', 'median', 'std']
    }).reset_index()

    phyto_species.columns = ['species', 'genus', 'gene_count',
                             'mean_transcripts', 'median_transcripts', 'std_transcripts',
                             'mean_exons', 'median_exons', 'std_exons']

    for col in ['mean_transcripts', 'median_transcripts', 'std_transcripts',
                'mean_exons', 'median_exons', 'std_exons']:
        phyto_species[col] = phyto_species[col].round(3)

    phyto_species = phyto_species.sort_values('gene_count', ascending=False)

    phyto_species_path = OUTPUT_DIR / "summary_by_species_phytopathogen.tsv"
    phyto_species.to_csv(phyto_species_path, sep='\t', index=False)
    print(f"  [DONE] Saved: {phyto_species_path}")
    print(f"    Phytopathogen species: {len(phyto_species)}")

    # ===== Summary statistics =====
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    print("\nAll FungiDB Species:")
    print(f"  Total species: {len(all_species)}")
    print(f"  Total genes: {all_species['gene_count'].sum():,}")
    print(f"  Mean transcripts per gene: {all_species['mean_transcripts'].mean():.3f}")
    print(f"  Mean exons per gene: {all_species['mean_exons'].mean():.3f}")

    print("\nPhytopathogen Species:")
    print(f"  Total species: {len(phyto_species)}")
    print(f"  Total genes: {phyto_species['gene_count'].sum():,}")
    print(f"  Mean transcripts per gene: {phyto_species['mean_transcripts'].mean():.3f}")
    print(f"  Mean exons per gene: {phyto_species['mean_exons'].mean():.3f}")

    # Top 10 species by gene count
    print("\nTop 10 Phytopathogen Species by Gene Count:")
    print(phyto_species[['species', 'gene_count', 'mean_transcripts', 'mean_exons']].head(10).to_string(index=False))


if __name__ == "__main__":
    main()
