#!/usr/bin/env python3
"""
Plot Old vs New Annotation comparison for Psauron and pLDDT scores.

Left panel: Psauron scores (blue) - X = new annotation (NCBI RefSeq), Y = old annotation (FungiDB v68)
Right panel: pLDDT scores (orange) - X = new annotation (NCBI RefSeq), Y = old annotation (FungiDB v68)

Note: In the data, ref_ columns = NCBI (NEW), qry_ columns = FungiDB (OLD)

Usage:
    python plot_oldvsnew_psauron_plddt.py
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from scipy import stats
from typing import List, Optional


def add_regression_line(ax, x, y, color='red', linestyle='-', alpha=0.8, label_pos='lower right'):
    """Add regression line with equation and R² to plot."""
    # Remove NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean, y_clean = x[mask], y[mask]

    if len(x_clean) < 2:
        return

    slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)

    # Plot regression line
    x_line = np.array([x_clean.min(), x_clean.max()])
    y_line = slope * x_line + intercept
    ax.plot(x_line, y_line, color=color, linestyle=linestyle, linewidth=2, alpha=alpha)

    # Add equation text
    eq_text = f'y = {slope:.3f}x + {intercept:.3f}\nR² = {r_value**2:.3f}'

    # Position based on label_pos
    if label_pos == 'lower right':
        ax.text(0.95, 0.05, eq_text, transform=ax.transAxes, fontsize=8,
                ha='right', va='bottom', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# Configuration
GENE_LEVEL_WITH_PSAURON = Path("output/figures_out/120126_all_out/gene_level_with_psauron.tsv")
PROTEINX_REF = Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/proteinx/GCF_013085055.1_proteinx.tsv")
PROTEINX_QRY = Path("/Users/sadik/Documents/projects/FungiDB/foc47/output/proteinx/Foc47_013085055.1_proteinx.tsv")
TRANSCRIPT_WITH_PSAURON = Path("output/figures_out/120126_all_out/transcript_level_with_psauron.tsv")
OUTPUT_DIR = Path("output/figures_out/120126_all_out")
DPI = 150


def main():
    print("Loading data...")

    # Load gene-level Psauron data
    gene_df = pd.read_csv(GENE_LEVEL_WITH_PSAURON, sep='\t')
    print(f"  Gene-level data: {len(gene_df)} gene pairs")

    # Load ProteinX pLDDT data
    proteinx_ref = pd.read_csv(PROTEINX_REF, sep='\t')
    proteinx_qry = pd.read_csv(PROTEINX_QRY, sep='\t')
    print(f"  ProteinX ref: {len(proteinx_ref)}, qry: {len(proteinx_qry)}")

    # Clean transcript IDs from ProteinX
    proteinx_ref['transcript_id'] = proteinx_ref['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)
    proteinx_qry['transcript_id'] = proteinx_qry['gene_name'].str.replace(r'_sample_\d+$', '', regex=True)

    # Load transcript-level data to map transcripts to gene pairs
    trans_df = pd.read_csv(TRANSCRIPT_WITH_PSAURON, sep='\t')

    # Merge ref pLDDT with transcript data to get gene mapping
    ref_trans_plddt = proteinx_ref[['transcript_id', 'residue_plddt_mean']].merge(
        trans_df[['old_transcript', 'old_gene', 'new_gene']].rename(
            columns={'old_transcript': 'transcript_id'}),
        on='transcript_id', how='inner'
    )

    # Merge query pLDDT with transcript data
    qry_trans_plddt = proteinx_qry[['transcript_id', 'residue_plddt_mean']].merge(
        trans_df[['new_transcript', 'old_gene', 'new_gene']].rename(
            columns={'new_transcript': 'transcript_id'}),
        on='transcript_id', how='inner'
    )

    # Aggregate pLDDT to gene level (mean of transcript pLDDT per gene pair)
    old_gene_plddt = ref_trans_plddt.groupby(['old_gene', 'new_gene']).agg({
        'residue_plddt_mean': 'mean'
    }).reset_index().rename(columns={'residue_plddt_mean': 'ref_plddt_mean'})

    qry_gene_plddt = qry_trans_plddt.groupby(['old_gene', 'new_gene']).agg({
        'residue_plddt_mean': 'mean'
    }).reset_index().rename(columns={'residue_plddt_mean': 'qry_plddt_mean'})

    # Merge all data
    ref_col = 'ref_psauron_score_mean'
    qry_col = 'qry_psauron_score_mean'

    combined = gene_df[['old_gene', 'new_gene', ref_col, qry_col,
                        'mapping_type', 'class_type_gene']].copy()
    combined = combined.merge(old_gene_plddt, on=['old_gene', 'new_gene'], how='left')
    combined = combined.merge(qry_gene_plddt, on=['old_gene', 'new_gene'], how='left')

    # Filter to gene pairs with all scores
    valid_pairs = combined.dropna(subset=[ref_col, qry_col, 'ref_plddt_mean', 'qry_plddt_mean'])
    print(f"  Gene pairs with all scores: {len(valid_pairs)}")

    # ===== Create plot =====
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left panel: Psauron scores (Old vs New) - BLUE
    ax1 = axes[0]
    ax1.scatter(valid_pairs[ref_col], valid_pairs[qry_col],
               alpha=0.3, s=15, c='#1f77b4')  # blue
    ax1.set_xlabel('New Annotation Psauron Score')
    ax1.set_ylabel('Old Annotation Psauron Score')
    ax1.set_title(f'Psauron Score: New vs Old (n={len(valid_pairs)} gene pairs)')
    ax1.set_xlim(0, 1.05)
    ax1.set_ylim(0, 1.05)
    # Add diagonal reference line
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='y=x')
    # Add regression line
    add_regression_line(ax1, valid_pairs[ref_col].values, valid_pairs[qry_col].values, color='red')

    # Right panel: pLDDT scores (Old vs New) - ORANGE
    ax2 = axes[1]
    ax2.scatter(valid_pairs['ref_plddt_mean'], valid_pairs['qry_plddt_mean'],
               alpha=0.3, s=15, c='#ff7f0e')  # orange
    ax2.set_xlabel('New Annotation pLDDT Score')
    ax2.set_ylabel('Old Annotation pLDDT Score')
    ax2.set_title(f'pLDDT Score: New vs Old (n={len(valid_pairs)} gene pairs)')
    # Add diagonal reference line
    plddt_min = min(valid_pairs['ref_plddt_mean'].min(), valid_pairs['qry_plddt_mean'].min()) - 5
    plddt_max = max(valid_pairs['ref_plddt_mean'].max(), valid_pairs['qry_plddt_mean'].max()) + 5
    ax2.plot([plddt_min, plddt_max], [plddt_min, plddt_max], 'k--', alpha=0.3, label='y=x')
    # Add regression line
    add_regression_line(ax2, valid_pairs['ref_plddt_mean'].values, valid_pairs['qry_plddt_mean'].values, color='red')

    # Add source traceability
    fig.text(0.99, 0.01, 'Source: plot_oldvsnew_psauron_plddt.py',
             fontsize=7, ha='right', va='bottom', alpha=0.5, style='italic')

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)

    output_path = OUTPUT_DIR / "annotation_comparison_psauron_plddt.png"
    fig.savefig(output_path, dpi=DPI, bbox_inches='tight')
    plt.close(fig)
    print(f"\n[DONE] Saved: {output_path}")

    # Print summary statistics
    corr_psauron = valid_pairs[ref_col].corr(valid_pairs[qry_col])
    corr_plddt = valid_pairs['ref_plddt_mean'].corr(valid_pairs['qry_plddt_mean'])
    print(f"\nSummary:")
    print(f"  Psauron correlation (new vs old): r = {corr_psauron:.3f}")
    print(f"  pLDDT correlation (new vs old): r = {corr_plddt:.3f}")
    print(f"  New (NCBI) Psauron mean: {valid_pairs[ref_col].mean():.3f}")
    print(f"  Old (FungiDB) Psauron mean: {valid_pairs[qry_col].mean():.3f}")
    print(f"  New (NCBI) pLDDT mean: {valid_pairs['ref_plddt_mean'].mean():.1f}")
    print(f"  Old (FungiDB) pLDDT mean: {valid_pairs['qry_plddt_mean'].mean():.1f}")

    # ===== Variant by Mapping Type =====
    print("\nGenerating variant by mapping type...")
    mapping_types = ['1to1', '1to2N', '1to2N+', 'Nto1', 'complex']
    mapping_colors = {
        '1to1': '#1f77b4', '1to2N': '#ff7f0e', '1to2N+': '#2ca02c',
        'Nto1': '#d62728', 'complex': '#9467bd'
    }
    mapping_labels = {
        '1to1': '1:1', '1to2N': '1:2N', '1to2N+': '1:2N+',
        'Nto1': 'N:1', 'complex': 'complex'
    }

    fig_mt, axes_mt = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Psauron by mapping type
    ax1 = axes_mt[0]
    for mtype in mapping_types:
        subset = valid_pairs[valid_pairs['mapping_type'] == mtype]
        if len(subset) > 0:
            ax1.scatter(subset[ref_col], subset[qry_col],
                       alpha=0.4, s=20, c=mapping_colors.get(mtype, 'gray'),
                       label=f'{mapping_labels[mtype]} (n={len(subset)})')
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.3)
    # Add overall regression line
    add_regression_line(ax1, valid_pairs[ref_col].values, valid_pairs[qry_col].values, color='red')
    ax1.set_xlabel('New Annotation Psauron Score')
    ax1.set_ylabel('Old Annotation Psauron Score')
    ax1.set_title('Psauron Score by Mapping Type')
    ax1.set_xlim(0, 1.05)
    ax1.set_ylim(0, 1.05)
    ax1.legend(fontsize=8)

    # Right: pLDDT by mapping type
    ax2 = axes_mt[1]
    for mtype in mapping_types:
        subset = valid_pairs[valid_pairs['mapping_type'] == mtype]
        if len(subset) > 0:
            ax2.scatter(subset['ref_plddt_mean'], subset['qry_plddt_mean'],
                       alpha=0.4, s=20, c=mapping_colors.get(mtype, 'gray'),
                       label=f'{mapping_labels[mtype]} (n={len(subset)})')
    ax2.plot([plddt_min, plddt_max], [plddt_min, plddt_max], 'k--', alpha=0.3)
    # Add overall regression line
    add_regression_line(ax2, valid_pairs['ref_plddt_mean'].values, valid_pairs['qry_plddt_mean'].values, color='red')
    ax2.set_xlabel('New Annotation pLDDT Score')
    ax2.set_ylabel('Old Annotation pLDDT Score')
    ax2.set_title('pLDDT Score by Mapping Type')
    ax2.legend(fontsize=8)

    fig_mt.text(0.99, 0.01, 'Source: plot_oldvsnew_psauron_plddt.py',
                fontsize=7, ha='right', va='bottom', alpha=0.5, style='italic')
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)

    mt_path = OUTPUT_DIR / "annotation_comparison_by_mapping_type.png"
    fig_mt.savefig(mt_path, dpi=DPI, bbox_inches='tight')
    plt.close(fig_mt)
    print(f"[DONE] Saved: {mt_path}")

    # ===== Variant by Class Type =====
    print("Generating variant by class type...")
    top_classes = valid_pairs['class_type_gene'].value_counts().head(6).index.tolist()

    fig_ct, axes_ct = plt.subplots(1, 2, figsize=(14, 6))

    # Left: Psauron by class type
    ax1 = axes_ct[0]
    for i, ctype in enumerate(top_classes):
        subset = valid_pairs[valid_pairs['class_type_gene'] == ctype]
        if len(subset) > 0:
            ax1.scatter(subset[ref_col], subset[qry_col],
                       alpha=0.4, s=20, color=plt.cm.tab10(i/10),
                       label=f'{ctype} (n={len(subset)})')
    ax1.plot([0, 1], [0, 1], 'k--', alpha=0.3)
    # Add overall regression line
    add_regression_line(ax1, valid_pairs[ref_col].values, valid_pairs[qry_col].values, color='red')
    ax1.set_xlabel('New Annotation Psauron Score')
    ax1.set_ylabel('Old Annotation Psauron Score')
    ax1.set_title('Psauron Score by Class Type')
    ax1.set_xlim(0, 1.05)
    ax1.set_ylim(0, 1.05)
    ax1.legend(fontsize=7, loc='upper left')

    # Right: pLDDT by class type
    ax2 = axes_ct[1]
    for i, ctype in enumerate(top_classes):
        subset = valid_pairs[valid_pairs['class_type_gene'] == ctype]
        if len(subset) > 0:
            ax2.scatter(subset['ref_plddt_mean'], subset['qry_plddt_mean'],
                       alpha=0.4, s=20, color=plt.cm.tab10(i/10),
                       label=f'{ctype} (n={len(subset)})')
    ax2.plot([plddt_min, plddt_max], [plddt_min, plddt_max], 'k--', alpha=0.3)
    # Add overall regression line
    add_regression_line(ax2, valid_pairs['ref_plddt_mean'].values, valid_pairs['qry_plddt_mean'].values, color='red')
    ax2.set_xlabel('New Annotation pLDDT Score')
    ax2.set_ylabel('Old Annotation pLDDT Score')
    ax2.set_title('pLDDT Score by Class Type')
    ax2.legend(fontsize=7, loc='upper left')

    fig_ct.text(0.99, 0.01, 'Source: plot_oldvsnew_psauron_plddt.py',
                fontsize=7, ha='right', va='bottom', alpha=0.5, style='italic')
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)

    ct_path = OUTPUT_DIR / "annotation_comparison_by_class_type.png"
    fig_ct.savefig(ct_path, dpi=DPI, bbox_inches='tight')
    plt.close(fig_ct)
    print(f"[DONE] Saved: {ct_path}")

    # ===== Variant: Faceted by Mapping Type x Class Type =====
    print("Generating faceted variant (mapping x class)...")
    mapping_types_present = [m for m in mapping_types if m in valid_pairs['mapping_type'].values]
    top_3_classes = valid_pairs['class_type_gene'].value_counts().head(3).index.tolist()

    if len(mapping_types_present) > 0 and len(top_3_classes) > 0:
        fig_comb, axes_comb = plt.subplots(len(mapping_types_present), 2,
                                          figsize=(12, 3 * len(mapping_types_present)))

        if len(mapping_types_present) == 1:
            axes_comb = axes_comb.reshape(1, -1)

        for row_idx, mtype in enumerate(mapping_types_present):
            mtype_data = valid_pairs[valid_pairs['mapping_type'] == mtype]

            # Left: Psauron
            ax_psauron = axes_comb[row_idx, 0]
            for i, ctype in enumerate(top_3_classes):
                subset = mtype_data[mtype_data['class_type_gene'] == ctype]
                if len(subset) > 0:
                    ax_psauron.scatter(subset[ref_col], subset[qry_col],
                                      alpha=0.5, s=15, color=plt.cm.tab10(i/10), label=ctype)
            ax_psauron.plot([0, 1], [0, 1], 'k--', alpha=0.3)
            ax_psauron.set_xlim(0, 1.05)
            ax_psauron.set_ylim(0, 1.05)
            ax_psauron.set_ylabel('Old Annotation Psauron Score')
            ax_psauron.set_title(f'Psauron - {mapping_labels[mtype]}')
            if row_idx == 0:
                ax_psauron.legend(fontsize=6, loc='lower right')
            if row_idx == len(mapping_types_present) - 1:
                ax_psauron.set_xlabel('New Annotation Psauron Score')

            # Right: pLDDT
            ax_plddt = axes_comb[row_idx, 1]
            for i, ctype in enumerate(top_3_classes):
                subset = mtype_data[mtype_data['class_type_gene'] == ctype]
                if len(subset) > 0:
                    ax_plddt.scatter(subset['ref_plddt_mean'], subset['qry_plddt_mean'],
                                    alpha=0.5, s=15, color=plt.cm.tab10(i/10), label=ctype)
            ax_plddt.plot([plddt_min, plddt_max], [plddt_min, plddt_max], 'k--', alpha=0.3)
            ax_plddt.set_title(f'pLDDT - {mapping_labels[mtype]}')
            if row_idx == len(mapping_types_present) - 1:
                ax_plddt.set_xlabel('New Annotation pLDDT Score')

        fig_comb.text(0.99, 0.01, 'Source: plot_oldvsnew_psauron_plddt.py',
                     fontsize=7, ha='right', va='bottom', alpha=0.5, style='italic')
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.05)

        comb_path = OUTPUT_DIR / "annotation_comparison_by_mapping_and_class.png"
        fig_comb.savefig(comb_path, dpi=DPI, bbox_inches='tight')
        plt.close(fig_comb)
        print(f"[DONE] Saved: {comb_path}")


def plot_psauron_scatter(
    df: pd.DataFrame,
    output_path: Path,
    ref_col: str = 'ref_psauron_score_mean',
    qry_col: str = 'qry_psauron_score_mean',
    color_by: Optional[str] = None,
    config: dict = None
) -> Optional[Path]:
    """
    Generate Psauron score scatter plot (new vs old annotation).

    Args:
        df: DataFrame with Psauron score columns
        output_path: Path to save the figure
        ref_col: Column name for new annotation (NCBI RefSeq)
        qry_col: Column name for old annotation (FungiDB)
        color_by: Optional column to color by (mapping_type or class_type_gene)
        config: Optional configuration

    Returns:
        Path to output file, or None if failed
    """
    config = config or {'figure_dpi': 150}

    # Filter valid data
    valid = df.dropna(subset=[ref_col, qry_col])
    if len(valid) == 0:
        print("  [ERROR] No valid Psauron data")
        return None

    fig, ax = plt.subplots(figsize=(10, 8))

    if color_by and color_by in valid.columns:
        categories = valid[color_by].value_counts().head(6).index.tolist()
        for i, cat in enumerate(categories):
            subset = valid[valid[color_by] == cat]
            ax.scatter(subset[ref_col], subset[qry_col],
                      alpha=0.4, s=20, color=plt.cm.tab10(i/10),
                      label=f'{cat} (n={len(subset)})')
        ax.legend(fontsize=8, loc='upper left')
    else:
        ax.scatter(valid[ref_col], valid[qry_col],
                  alpha=0.3, s=15, c='#1f77b4')

    # Diagonal and regression
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='y=x')
    add_regression_line(ax, valid[ref_col].values, valid[qry_col].values, color='red')

    ax.set_xlabel('New Annotation Psauron Score')
    ax.set_ylabel('Old Annotation Psauron Score')
    ax.set_title(f'Psauron Score Distribution (n={len(valid)} gene pairs)')
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.05)

    plt.tight_layout()
    fig.savefig(output_path, dpi=config.get('figure_dpi', 150), bbox_inches='tight')
    plt.close(fig)

    print(f"  [DONE] Saved: {output_path}")
    return output_path


def generate_quality_score_plots(
    gene_level_file: str,
    output_dir: Path,
    config: dict = None
) -> List[Path]:
    """
    Generate quality score comparison plots for CLI integration.

    Args:
        gene_level_file: Path to gene-level TSV with Psauron columns
        output_dir: Directory to save plots
        config: Optional configuration

    Returns:
        List of generated plot file paths
    """
    generated_files = []
    config = config or {'figure_dpi': 150}

    if not Path(gene_level_file).exists():
        print(f"  [ERROR] File not found: {gene_level_file}")
        return generated_files

    print(f"  Loading: {gene_level_file}")
    df = pd.read_csv(gene_level_file, sep='\t')
    print(f"    Loaded {len(df):,} gene pairs")

    # Check for Psauron columns (support both naming conventions)
    ref_col = 'ref_psauron_score_mean' if 'ref_psauron_score_mean' in df.columns else 'new_psauron_score_mean'
    qry_col = 'qry_psauron_score_mean' if 'qry_psauron_score_mean' in df.columns else 'old_psauron_score_mean'

    if ref_col not in df.columns or qry_col not in df.columns:
        print("  [WARN] Psauron columns not found, skipping quality plots")
        print(f"    Looking for: ref_psauron_score_mean or new_psauron_score_mean")
        print(f"    Looking for: qry_psauron_score_mean or old_psauron_score_mean")
        return generated_files

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Basic scatter plot
    path = plot_psauron_scatter(
        df, output_dir / 'psauron_scatter.png',
        ref_col=ref_col, qry_col=qry_col, config=config
    )
    if path:
        generated_files.append(path)

    # By mapping type
    if 'mapping_type' in df.columns:
        path = plot_psauron_scatter(
            df, output_dir / 'psauron_by_mapping_type.png',
            ref_col=ref_col, qry_col=qry_col,
            color_by='mapping_type', config=config
        )
        if path:
            generated_files.append(path)

    # By class type
    if 'class_type_gene' in df.columns:
        path = plot_psauron_scatter(
            df, output_dir / 'psauron_by_class_type.png',
            ref_col=ref_col, qry_col=qry_col,
            color_by='class_type_gene', config=config
        )
        if path:
            generated_files.append(path)

    return generated_files


if __name__ == "__main__":
    main()
