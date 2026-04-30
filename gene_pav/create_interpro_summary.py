#!/usr/bin/env python3
"""
Generate InterPro summary statistics for F. oxysporum old vs new annotations.

Analyzes InterProScan TSV output files to calculate:
- Total number of proteins
- Number of proteins with at least one InterPro domain  
- Percentage of proteins with InterPro domains

Usage:
    python create_interpro_summary.py
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# File paths
OLD_INTERPRO = "/Users/sadik/Documents/projects/FungiDB/foc47/output/inteproscan/foc67_v68.prot.faa.tsv"
NEW_INTERPRO = "/Users/sadik/Documents/projects/FungiDB/foc47/output/inteproscan/GCF_013085055.1.prot.faa.tsv"
OUTPUT_DIR = "plots"

def load_interpro_data(filepath, annotation_name):
    """Load InterProScan TSV output file"""
    print(f"Loading InterPro data for {annotation_name}: {filepath}")

    if not Path(filepath).exists():
        print(f"ERROR: File not found - {filepath}")
        return None

    try:
        # InterProScan TSV standard columns
        columns = [
            'protein_accession', 'sequence_md5', 'sequence_length', 'analysis',
            'signature_accession', 'signature_description', 'start_location', 
            'stop_location', 'score', 'status', 'date', 'interpro_accession', 
            'interpro_description'
        ]

        df = pd.read_csv(filepath, sep='\t', header=None, names=columns)
        print(f"Loaded {len(df)} InterPro records")
        return df

    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None

def analyze_interpro_summary(df, annotation_name):
    """Analyze InterPro domain coverage"""
    if df is None:
        return None

    print(f"\n=== {annotation_name} InterPro Analysis ===")

    # Get unique proteins
    unique_proteins = set(df['protein_accession'])
    total_proteins = len(unique_proteins)

    # Get proteins with actual InterPro domains (containing 'IPR' accessions)
    proteins_with_domains = set(df[df['interpro_accession'].str.contains('IPR', na=False)]['protein_accession'])
    proteins_with_domains_count = len(proteins_with_domains)

    # Calculate percentage
    percentage_with_domains = (proteins_with_domains_count / total_proteins) * 100 if total_proteins > 0 else 0

    # Count unique InterPro domains and total hits
    unique_domains = df[df['interpro_accession'].str.contains('IPR', na=False)]['interpro_accession'].nunique()
    total_domain_hits = len(df[df['interpro_accession'].str.contains('IPR', na=False)])

    stats = {
        'annotation_name': annotation_name,
        'total_proteins': total_proteins,
        'proteins_with_domains': proteins_with_domains_count,
        'percentage_with_domains': percentage_with_domains,
        'unique_interpro_domains': unique_domains,
        'total_domain_hits': total_domain_hits
    }

    print(f"  Total proteins: {total_proteins:,}")
    print(f"  Proteins with InterPro domains: {proteins_with_domains_count:,}")
    print(f"  Percentage with domains: {percentage_with_domains:.1f}%")
    print(f"  Unique InterPro domains: {unique_domains:,}")

    return stats

def create_interpro_plot(old_stats, new_stats, output_dir):
    """Create InterPro comparison plot"""
    if old_stats is None or new_stats is None:
        print("ERROR: Missing statistics for plot")
        return None

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Bar chart comparison
    categories = ['Total\nProteins', 'With InterPro\nDomains', 'Without InterPro\nDomains']
    
    old_values = [
        old_stats['total_proteins'],
        old_stats['proteins_with_domains'],
        old_stats['total_proteins'] - old_stats['proteins_with_domains']
    ]
    
    new_values = [
        new_stats['total_proteins'],
        new_stats['proteins_with_domains'], 
        new_stats['total_proteins'] - new_stats['proteins_with_domains']
    ]

    x = range(len(categories))
    width = 0.35

    ax1.bar([i - width/2 for i in x], old_values, width, 
            label='Old (foc67_v68)', color='#ff9999')
    ax1.bar([i + width/2 for i in x], new_values, width,
            label='New (GCF_013085055.1)', color='#99ccff')

    ax1.set_ylabel('Number of Proteins')
    ax1.set_title('InterPro Domain Coverage\nF. oxysporum Old vs New')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories)
    ax1.legend()

    # Add value labels
    for i, (old_val, new_val) in enumerate(zip(old_values, new_values)):
        ax1.text(i - width/2, old_val + max(old_values)*0.01, f'{old_val:,}', 
                ha='center', va='bottom', fontsize=9)
        ax1.text(i + width/2, new_val + max(new_values)*0.01, f'{new_val:,}',
                ha='center', va='bottom', fontsize=9)

    # Percentage comparison
    annotations = ['Old\n(foc67_v68)', 'New\n(GCF_013085055.1)']
    percentages = [old_stats['percentage_with_domains'], new_stats['percentage_with_domains']]
    colors = ['#ff9999', '#99ccff']

    bars = ax2.bar(annotations, percentages, color=colors)
    ax2.set_ylabel('Percentage (%)')
    ax2.set_title('Percentage of Proteins\nwith InterPro Domains')
    ax2.set_ylim(0, 100)

    # Add percentage labels
    for bar, pct in zip(bars, percentages):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')

    plt.tight_layout()

    # Save plot
    output_path = Path(output_dir) / "interpro_summary.png"
    output_path.parent.mkdir(exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nInterPro plot saved to: {output_path}")

    return output_path

def print_summary_table(old_stats, new_stats):
    """Print formatted summary table"""
    if old_stats is None or new_stats is None:
        return

    print(f"\n{'='*70}")
    print("F. OXYSPORUM INTERPRO DOMAIN SUMMARY")
    print(f"{'='*70}")
    print(f"{'Metric':<35} {'Old (foc67_v68)':<15} {'New (GCF_013085055.1)':<15}")
    print(f"{'-'*70}")
    print(f"{'Total proteins':<35} {old_stats['total_proteins']:,<15} {new_stats['total_proteins']:,<15}")
    print(f"{'With InterPro domains':<35} {old_stats['proteins_with_domains']:,<15} {new_stats['proteins_with_domains']:,<15}")
    print(f"{'Without InterPro domains':<35} {old_stats['total_proteins']-old_stats['proteins_with_domains']:,<15} {new_stats['total_proteins']-new_stats['proteins_with_domains']:,<15}")
    print(f"{'Percentage with domains':<35} {old_stats['percentage_with_domains']:.1f}%{'':<11} {new_stats['percentage_with_domains']:.1f}%{'':<11}")
    print(f"{'Unique InterPro domains':<35} {old_stats['unique_interpro_domains']:,<15} {new_stats['unique_interpro_domains']:,<15}")
    print(f"{'='*70}")

def main():
    """Main analysis function"""
    print("=== F. oxysporum InterPro Domain Analysis ===\n")

    # Load data
    old_df = load_interpro_data(OLD_INTERPRO, "Old (foc67_v68)")
    new_df = load_interpro_data(NEW_INTERPRO, "New (GCF_013085055.1)")

    # Analyze
    old_stats = analyze_interpro_summary(old_df, "Old (foc67_v68)") if old_df is not None else None
    new_stats = analyze_interpro_summary(new_df, "New (GCF_013085055.1)") if new_df is not None else None

    if old_stats and new_stats:
        create_interpro_plot(old_stats, new_stats, OUTPUT_DIR)
        print_summary_table(old_stats, new_stats)
        print(f"\n=== Analysis Complete ===")
    else:
        print("ERROR: Could not load InterPro data files")

if __name__ == "__main__":
    main()
