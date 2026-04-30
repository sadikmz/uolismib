#!/usr/bin/env python3
"""
Create GFF-based DIAMOND BLASTP Venn diagram showing protein similarities
between F. oxysporum old vs new annotations.

Uses actual gene counts from GFF files and DIAMOND BLASTP similarity from PAVprot.

Usage:
    python create_gff_based_blastp_venn.py [--min-pident 50] [--min-coverage 70]
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib_venn import venn2, venn2_circles
import seaborn as sns
import argparse
from pathlib import Path
import numpy as np
# Using simple GFF parser instead of gffutils
from collections import defaultdict

# File paths
OLD_GFF = "/Users/sadik/Documents/projects/FungiDB/foc47/data/plot/FungiDB-68_Fo47.gff"
NEW_GFF = "/Users/sadik/Documents/projects/FungiDB/foc47/data/plot/GCF_013085055.1.gff"
PAVPROT_OUTPUT = "tmp/pavprot_out_20260209_154955/gene_level_enriched_all.tsv"
OUTPUT_DIR = "plots"

# Default parameters
DEFAULT_MIN_PIDENT = 50.0
DEFAULT_MIN_COVERAGE = 70.0

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Create GFF-based BLASTP Venn diagram for F. oxysporum proteins'
    )
    parser.add_argument('--min-pident', type=float, default=DEFAULT_MIN_PIDENT,
                       help=f'Minimum percent identity threshold (default: {DEFAULT_MIN_PIDENT})')
    parser.add_argument('--min-coverage', type=float, default=DEFAULT_MIN_COVERAGE,
                       help=f'Minimum coverage threshold (default: {DEFAULT_MIN_COVERAGE})')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                       help=f'Output directory (default: {OUTPUT_DIR})')
    parser.add_argument('--old-gff', type=str, default=OLD_GFF,
                       help=f'Old annotation GFF file (default: {OLD_GFF})')
    parser.add_argument('--new-gff', type=str, default=NEW_GFF,
                       help=f'New annotation GFF file (default: {NEW_GFF})')
    parser.add_argument('--pavprot-file', type=str, default=PAVPROT_OUTPUT,
                       help=f'PAVprot output file (default: {PAVPROT_OUTPUT})')

    return parser.parse_args()

def parse_gff_simple(gff_file):
    """
    Simple GFF parser to extract gene IDs from protein-coding genes.
    Correctly handles different GFF annotation formats.
    """
    print(f"Parsing GFF file: {gff_file}")

    genes = set()
    try:
        with open(gff_file, 'r') as f:
            for line_num, line in enumerate(f):
                if line.startswith('#'):
                    continue

                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue

                feature_type = parts[2]
                attributes = parts[8]

                # Handle different annotation formats
                if feature_type == 'protein_coding_gene':
                    # Old annotation format (FungiDB)
                    if 'ID=' in attributes:
                        for attr in attributes.split(';'):
                            if attr.startswith('ID='):
                                gene_id = attr.replace('ID=', '').strip()
                                genes.add(gene_id)
                                break

                elif feature_type == 'gene':
                    # New annotation format (NCBI RefSeq)
                    # Check if it's a protein-coding gene (exclude pseudogenes)
                    is_protein_coding = True
                    gene_id = None

                    for attr in attributes.split(';'):
                        if attr.startswith('ID='):
                            gene_id = attr.replace('ID=', '').strip()
                        elif attr.startswith('gbkey='):
                            gbkey = attr.replace('gbkey=', '').strip()
                            if gbkey != 'Gene':
                                is_protein_coding = False
                        elif 'pseudogene' in attr:
                            is_protein_coding = False

                    if gene_id and is_protein_coding:
                        genes.add(gene_id)

                if line_num % 10000 == 0 and line_num > 0:
                    print(f"  Processed {line_num:,} lines...")

    except Exception as e:
        print(f"Error parsing GFF: {e}")
        return set()

    print(f"  Found {len(genes):,} unique protein-coding genes")
    return genes

def load_pavprot_data(filepath):
    """Load PAVprot data with DIAMOND BLASTP results"""
    print(f"Loading PAVprot data from: {filepath}")
    df = pd.read_csv(filepath, sep='\t')
    print(f"Loaded {len(df)} gene mapping records")
    return df

def apply_blastp_filters(df, min_pident, min_coverage):
    """Apply BLASTP similarity filters to PAVprot data"""
    print(f"\nApplying BLASTP filters:")
    print(f"  Minimum percent identity: {min_pident}%")
    print(f"  Minimum coverage: {min_coverage}%")

    initial_count = len(df)

    # Filter by percent identity and coverage
    df_filtered = df[
        (df['pident'] >= min_pident) &
        (df['qcovhsp'] >= min_coverage) &
        (df['scovhsp'] >= min_coverage)
    ].copy()

    filtered_count = len(df_filtered)

    print(f"  Initial records: {initial_count:,}")
    print(f"  After BLASTP filters: {filtered_count:,}")
    print(f"  Filtered out: {initial_count - filtered_count:,} ({((initial_count - filtered_count) / initial_count * 100):.1f}%)")

    return df_filtered

def normalize_gene_ids(gene_set, annotation_type):
    """Normalize gene IDs to handle different naming conventions"""
    normalized = set()

    for gene_id in gene_set:
        # Remove common prefixes/suffixes
        clean_id = gene_id

        if annotation_type == 'old':
            # Old annotation might have FOZG_ prefix
            if clean_id.startswith('gene-'):
                clean_id = clean_id.replace('gene-', '')
            # Keep original if it looks like FOZG_XXXXX

        elif annotation_type == 'new':
            # New annotation might have different format
            if clean_id.startswith('gene-'):
                clean_id = clean_id.replace('gene-', '')

        normalized.add(clean_id)

    return normalized

def analyze_gff_based_similarity(old_genes, new_genes, df_filtered, min_pident, min_coverage):
    """Analyze protein similarities using GFF gene counts and BLASTP results"""

    print(f"\n=== GFF-Based Analysis ===")
    print(f"GFF gene counts:")
    print(f"  Old annotation: {len(old_genes):,} genes")
    print(f"  New annotation: {len(new_genes):,} genes")

    # Get genes with BLASTP similarity from PAVprot
    old_genes_with_similarity = set(df_filtered['old_gene'].dropna())
    new_genes_with_similarity = set(df_filtered['new_gene'].dropna())

    print(f"\nBLASTP similarity matches:")
    print(f"  Old genes with matches: {len(old_genes_with_similarity):,}")
    print(f"  New genes with matches: {len(new_genes_with_similarity):,}")
    print(f"  Similar pairs: {len(df_filtered):,}")

    # Calculate overlaps and unique sets for Venn diagram
    # For Venn: we want to show genes with/without similar counterparts

    # Overlap: genes that have similar counterparts (conservative estimate)
    overlap_size = min(len(old_genes_with_similarity), len(new_genes_with_similarity))

    # Unique to old: old genes without similar matches in new
    old_unique = len(old_genes) - len(old_genes_with_similarity)

    # Unique to new: new genes without similar matches in old
    new_unique = len(new_genes) - len(new_genes_with_similarity)

    stats = {
        'total_old_genes': len(old_genes),
        'total_new_genes': len(new_genes),
        'old_with_similarity': len(old_genes_with_similarity),
        'new_with_similarity': len(new_genes_with_similarity),
        'old_unique': old_unique,
        'new_unique': new_unique,
        'overlap': overlap_size,
        'similar_pairs': len(df_filtered),
        'parameters': {
            'min_pident': min_pident,
            'min_coverage': min_coverage
        }
    }

    return stats

def create_gff_based_venn_diagram(stats, output_dir):
    """Create Venn diagram using actual GFF gene counts"""

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))  # Larger figure for bigger circles

    # Extract values for Venn diagram
    old_unique = stats['old_unique']
    new_unique = stats['new_unique']
    overlap = stats['overlap']

    print(f"\n=== Venn Diagram Statistics ===")
    print(f"  Old genes total: {stats['total_old_genes']:,}")
    print(f"  New genes total: {stats['total_new_genes']:,}")
    print(f"  Old genes with similar match: {stats['old_with_similarity']:,}")
    print(f"  New genes with similar match: {stats['new_with_similarity']:,}")
    print(f"  Old unique (no similar match): {old_unique:,}")
    print(f"  New unique (no similar match): {new_unique:,}")
    print(f"  Genes with similar counterparts: {overlap:,}")

    # Main Venn diagram with larger circles (controlled by figure size)
    venn = venn2(
        subsets=(old_unique, new_unique, overlap),
        set_labels=(f'Old Annotation\n({stats["total_old_genes"]:,} genes)',
                   f'New Annotation\n({stats["total_new_genes"]:,} genes)'),
        ax=ax1
    )

    # Customize colors
    if venn.get_patch_by_id('10'):
        venn.get_patch_by_id('10').set_color('#ff9999')  # Old unique
    if venn.get_patch_by_id('01'):
        venn.get_patch_by_id('01').set_color('#99ccff')  # New unique
    if venn.get_patch_by_id('11'):
        venn.get_patch_by_id('11').set_color('#99ff99')  # Similar

    # Add circles with thick, colored outlines
    circles = venn2_circles(subsets=(old_unique, new_unique, overlap),
                           linewidth=3.0,  # Extra thick outlines for visibility
                           ax=ax1)

    # Method 3: Proportional to Data (circle sizes reflect gene counts)
    # Calculate sizes based on actual gene counts
    old_ratio = stats['total_old_genes'] / max(stats['total_old_genes'], stats['total_new_genes'])
    new_ratio = stats['total_new_genes'] / max(stats['total_old_genes'], stats['total_new_genes'])

    # Scale to desired size range
    base_size = 0.4  # Adjust this to control overall circle size
    old_radius = base_size * old_ratio
    new_radius = base_size * new_ratio

    if circles[0]:  # Old annotation circle
        circles[0].set_radius(old_radius)
        circles[0].set_edgecolor('#cc0000')  # Dark red
    if circles[1]:  # New annotation circle
        circles[1].set_radius(new_radius)
        circles[1].set_edgecolor('#0000cc')  # Dark blue

    print(f"  Proportional circle sizes - Old: {old_radius:.3f} (ratio: {old_ratio:.3f}), New: {new_radius:.3f} (ratio: {new_ratio:.3f})")

    ax1.set_title(f'Protein Similarity based on DIAMOND BLASTP\n(≥{stats["parameters"]["min_pident"]}% identity, ≥{stats["parameters"]["min_coverage"]}% coverage)',
                 fontsize=14, fontweight='bold')

    # Summary bar chart
    categories = ['Total\nGenes\n(GFF)', 'With BLASTP\nSimilarity', 'Unique\n(No Match)']
    old_values = [stats['total_old_genes'], stats['old_with_similarity'], stats['old_unique']]
    new_values = [stats['total_new_genes'], stats['new_with_similarity'], stats['new_unique']]

    x = np.arange(len(categories))
    width = 0.35

    bars1 = ax2.bar(x - width/2, old_values, width, label='Old Annotation (FungiDB-68)', color='#ff9999')
    bars2 = ax2.bar(x + width/2, new_values, width, label='New Annotation (GCF_013085055.1)', color='#99ccff')

    ax2.set_xlabel('Gene Categories')
    ax2.set_ylabel('Number of Genes')
    ax2.set_title('Gene Count Comparison from GFF Files')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories)
    ax2.legend()

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{height:,}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9)

    # Add summary text
    coverage_old = (stats['old_with_similarity'] / stats['total_old_genes']) * 100
    coverage_new = (stats['new_with_similarity'] / stats['total_new_genes']) * 100

    summary_text = f"""
    BLASTP Similarity Parameters:
    • Min. Identity: {stats['parameters']['min_pident']}%
    • Min. Coverage: {stats['parameters']['min_coverage']}%

    Gene Coverage:
    • Old: {coverage_old:.1f}% genes with similarity
    • New: {coverage_new:.1f}% genes with similarity
    • Similar pairs found: {stats['similar_pairs']:,}
    """

    plt.figtext(0.02, 0.02, summary_text, fontsize=10,
               bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.8))

    plt.suptitle('Fusarium oxysporum Fo47 Protein Coding Genes Similarity\n Old vs New Annotations',
                fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout()

    # Save plot
    filename = f"foc_gff_blastp_venn_pident{stats['parameters']['min_pident']}_cov{stats['parameters']['min_coverage']}.png"
    output_path = Path(output_dir) / filename
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nGFF-based BLASTP Venn diagram saved to: {output_path}")

    return output_path

def main():
    """Main analysis function"""
    args = parse_arguments()

    print("=== F. oxysporum GFF-Based BLASTP Similarity Analysis ===\n")
    print(f"Parameters:")
    print(f"  Old GFF: {args.old_gff}")
    print(f"  New GFF: {args.new_gff}")
    print(f"  PAVprot file: {args.pavprot_file}")
    print(f"  Minimum percent identity: {args.min_pident}%")
    print(f"  Minimum coverage: {args.min_coverage}%")

    # Parse GFF files to get actual gene counts
    old_genes = parse_gff_simple(args.old_gff)
    new_genes = parse_gff_simple(args.new_gff)

    if len(old_genes) == 0 or len(new_genes) == 0:
        print("ERROR: Could not parse genes from GFF files")
        return

    # Load PAVprot BLASTP data
    df = load_pavprot_data(args.pavprot_file)

    # Apply BLASTP filters
    df_filtered = apply_blastp_filters(df, args.min_pident, args.min_coverage)

    # Analyze similarity using GFF counts
    stats = analyze_gff_based_similarity(old_genes, new_genes, df_filtered,
                                        args.min_pident, args.min_coverage)

    # Create Venn diagram
    venn_path = create_gff_based_venn_diagram(stats, args.output_dir)

    print(f"\n=== Analysis Complete ===")
    print(f"Generated file: {venn_path.name}")

    # Print final summary
    print(f"\n=== SUMMARY ===")
    print(f"  GFF-based gene counts:")
    print(f"    Old annotation: {stats['total_old_genes']:,} genes")
    print(f"    New annotation: {stats['total_new_genes']:,} genes")
    print(f"  BLASTP similarity matches:")
    print(f"    Old genes with matches: {stats['old_with_similarity']:,} ({(stats['old_with_similarity']/stats['total_old_genes']*100):.1f}%)")
    print(f"    New genes with matches: {stats['new_with_similarity']:,} ({(stats['new_with_similarity']/stats['total_new_genes']*100):.1f}%)")
    print(f"    Similar pairs found: {stats['similar_pairs']:,}")

if __name__ == "__main__":
    main()