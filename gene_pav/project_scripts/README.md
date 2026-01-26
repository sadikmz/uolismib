# Project Scripts

This folder contains **project-specific scripts** that demonstrate how to use the PAVprot pipeline for real analyses. These are templates/examples that you can adapt for your own projects.

## Quick Start

```bash
# 1. Copy the config template
cp config.yaml.template config.yaml

# 2. Edit config.yaml with your paths
#    (see Configuration section below)

# 3. Run the pipeline
python run_pipeline.py --config config.yaml --all
```

## Scripts

| Script | Purpose | Customization Needed |
|--------|---------|---------------------|
| `run_pipeline.py` | Master workflow orchestrator | Use `--config` flag or edit CONFIG dict |
| `run_emckmnje1_analysis.py` | Filtered analysis wrapper | Update input/output paths |
| `analyze_fungidb_species.py` | FungiDB species-level analysis | Update data file paths |
| `plot_oldvsnew_psauron_plddt.py` | Annotation comparison plots | Update input TSV paths |
| `plot_ipr_1to1_comparison.py` | IPR domain comparison for 1:1 orthologs | Update input/output paths |
| `plot_psauron_distribution.py` | Psauron score distribution plots | Update input/output paths |

## Configuration

### Option 1: Use config.yaml (Recommended)

```bash
# Copy template and edit
cp config.yaml.template config.yaml
nano config.yaml  # or your preferred editor

# Run with config file
python run_pipeline.py --config config.yaml --all
```

The config file includes:
- **Base directories** - project and output paths
- **PAVprot outputs** - transcript/gene level TSV files
- **External data** - Psauron, ProteinX, FungiDB paths
- **Annotation prefixes** - reference and query identifiers
- **Plot settings** - DPI, format, style

### Option 2: Edit CONFIG dict directly

For quick one-off runs, you can edit the `CONFIG` dictionary at the top of `run_pipeline.py`:

```python
CONFIG = {
    "gene_pav_dir": Path(__file__).parent,
    "output_dir": Path(__file__).parent / "pipeline_output",
    "psauron_ref": Path("/your/path/to/psauron/ref_all.csv"),
    # ... etc
}
```

## Usage Examples

```bash
# Run all tasks
python run_pipeline.py --config config.yaml --all

# Run specific task
python run_pipeline.py --config config.yaml --task plots

# List available tasks
python run_pipeline.py --list

# Dry run (show what would be done)
python run_pipeline.py --config config.yaml --all --dry-run
```

## Available Tasks

| Task | Description |
|------|-------------|
| `plots` | Generate all plots |
| `psauron` | Psauron quality score analysis |
| `proteinx` | ProteinX/pLDDT analysis |
| `fungidb` | FungiDB comparative analysis |
| `ipr` | InterPro domain analysis |
| `scenarios` | Scenario classification analysis |

## Note

These scripts were developed for the *Fusarium oxysporum* Fo47 analysis comparing NCBI RefSeq vs FungiDB v68 annotations. They serve as working examples of downstream analysis workflows built on top of the core PAVprot pipeline.

## Files

```
project_scripts/
├── config.yaml.template  # Configuration template (copy to config.yaml)
├── README.md             # This file
├── run_pipeline.py       # Master workflow orchestrator
├── run_emckmnje1_analysis.py
├── analyze_fungidb_species.py
├── plot_ipr_1to1_comparison.py
├── plot_oldvsnew_psauron_plddt.py
└── plot_psauron_distribution.py
```
