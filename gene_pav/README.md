# PAVprot - Gene Presence/Absence Variation Protein Analysis

> **Last Updated:** 2026-02-02

A comprehensive pipeline for analyzing gene annotation quality between old and new genome annotations using GffCompare tracking data.

## Quick Start

```bash
# Basic analysis
python pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff old.gff3,new.gff3 \
  --output-dir output/

# Full analysis with DIAMOND + BBH + InterProScan
python pavprot.py \
  --gff-comp gffcompare.tracking \
  --gff old.gff3,new.gff3 \
  --prot old.faa,new.faa \
  --run-diamond --run-bbh \
  --interproscan-out old_interpro.tsv,new_interpro.tsv
```

## Directory Structure

```
gene_pav/
├── pavprot.py                        # Main pipeline orchestrator
├── tools_runner.py                   # Unified external tools module
├── config.yaml                       # Pipeline configuration
├── requirements.txt                  # Python dependencies
│
├── # Core Analysis Modules (root level)
├── parse_interproscan.py             # InterProScan TSV parsing
├── bidirectional_best_hits.py        # BBH analysis
├── mapping_multiplicity.py           # 1:N mapping detection
├── gsmc.py                           # Gene Synteny Mapping Classifier
├── pairwise_align_prot.py            # Protein alignment
├── synonym_mapping_summary.py        # Summary statistics
├── inconsistent_genes_transcript_IPR_PAV.py  # IPR inconsistency detection
│
├── plot/                             # Visualization modules
│   ├── __init__.py
│   ├── config.py                     # Plot configuration
│   ├── utils.py                      # Shared plotting utilities
│   ├── plot_ipr_comparison.py        # IPR domain comparison
│   ├── plot_ipr_gene_level.py        # Gene-level visualization
│   ├── plot_ipr_shapes.py            # Shape-encoded scatter
│   ├── plot_ipr_advanced.py          # Advanced visualizations
│   ├── plot_ipr_proportional_bias.py # Bias analysis
│   └── plot_domain_comparison.py     # Before/after comparison
│
├── project_scripts/                  # Project-specific examples
│   ├── run_pipeline.py               # Example pipeline runner
│   └── ...
│
├── test/                             # Test suite
│   ├── test_pavprot.py
│   ├── test_all_outputs.py
│   └── data/                         # Test data files
│
└── docs/                             # Documentation
    ├── ARCHITECTURE.md
    ├── SCENARIOS.md
    └── ...
```

## Key Features

- **Gene Mapping Analysis**: Parse GffCompare tracking to identify gene relationships
- **Scenario Detection**: Classify orthology relationships (1:1, 1:N, N:1, cross-mapping)
- **DIAMOND Integration**: Protein sequence alignment with BBH analysis
- **InterProScan Support**: Domain-based annotation quality assessment
- **Comprehensive Plotting**: Multiple visualization options for results

## Biological Scenarios Detected

| Scenario | Description |
|----------|-------------|
| E | 1:1 orthologs (true orthology) |
| A | 1:N (one old → multiple new genes) |
| B | N:1 (multiple old → one new gene) |
| J | Complex 1:N (one old → 3+ new genes) |
| CDI | Cross-mapping groups |
| F | Positional swaps (adjacent gene inversions) |
| G | Unmapped old genes |
| H | Unmapped new genes |

## Output Files

| File | Description |
|------|-------------|
| `*_diamond_blastp.tsv` | Main transcript-level mapping output |
| `*_gene_level.tsv` | Gene-level aggregated output |
| `*_diamond_blastp.xlsx` | **Excel workbook** with all results (11 sheets) |
| `*_old_to_multiple_new.tsv` | One-to-many mapping analysis |
| `*_new_to_multiple_old.tsv` | Many-to-one mapping analysis |
| `*_total_ipr_length.tsv` | IPR domain lengths per gene |

### Excel Export (Default: Enabled)

All results are automatically exported to a single Excel workbook with 11 sheets:
- `transcript_level`, `gene_level` - Main outputs
- `old_to_multi_new`, `new_to_multi_old` - Mapping analysis
- `old_domain_dist`, `new_domain_dist` - Domain distributions
- `ipr_length` - Combined IPR lengths (with `source` column)
- `bbh_results` - Bidirectional best hits

Use `--no-output-excel` to disable Excel export.

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - Module connectivity and data flow
- [Scenarios](docs/SCENARIOS.md) - Biological scenario reference
- [Output Format](docs/OUTPUT_FORMAT.md) - Column descriptions
- [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) - Future improvements

## Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/gene_pav.git
cd gene_pav

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python pavprot.py --help
```

## Requirements

### Python Dependencies
- Python 3.8+
- pandas>=1.3.0
- numpy>=1.21.0
- Biopython>=1.79 (for protein alignment)
- matplotlib>=3.4.0, seaborn>=0.11.0 (for plotting)
- pyyaml>=5.4.0 (for configuration)
- openpyxl>=3.0.0 (for Excel export)

### External Tools (Optional)
- DIAMOND - for sequence alignment
- InterProScan - for domain detection
- gffcompare - for GFF comparison
- Liftoff - for annotation liftover
- BUSCO - for completeness assessment

## License

See LICENSE file for details.
