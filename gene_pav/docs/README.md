# PAVprot - Presence/Absence Variation Protein Analysis Pipeline

> **Last Updated:** 2026-02-09
> **Status**: Production Ready ✓

A comprehensive pipeline for analyzing gene annotation quality and presence/absence variation between old and new genome annotations using GffCompare tracking data. Complete with integrated plotting, data integration, and flexible visualization.

## Quick Start

### 1. List Available Plot Types
```bash
python gene_pav/src/pavprot.py --list
```

### 2. Generate Plots Only (from existing data)
```bash
python gene_pav/src/pavprot.py --plot-only \
  --dataset gene_pav/plots \
  --plot advanced
```

### 3. Run Complete Pipeline with Data Integration
```bash
python gene_pav/scripts/run_pipeline.py --task psauron
```

### 4. Full Analysis with All Features
```bash
python gene_pav/src/pavprot.py \
  --gff-comp tracking.txt \
  --gff old.gff3,new.gff3 \
  --prot old.faa,new.faa \
  --run-diamond \
  --plot scenarios ipr advanced
```

## Project Structure

```
gene_pav/
├── src/
│   └── pavprot.py              Main executable script
│
├── scripts/                    Accessory utility scripts (13)
│   ├── run_pipeline.py         Pipeline orchestration & data integration
│   ├── parse_interproscan.py   InterProScan domain annotation parser
│   ├── bidirectional_best_hits.py  BBH analysis
│   ├── gsmc.py                 Gene/scenario mapping classification
│   ├── mapping_multiplicity.py Detect 1:many, many:1 mappings
│   ├── pairwise_align_prot.py  Protein sequence alignment
│   ├── tools_runner.py         Tool execution wrapper
│   ├── parse_liftover_extra_copy_number.py  Copy number detection
│   ├── inconsistent_genes_transcript_IPR_PAV.py  Consistency checker
│   ├── synonym_mapping_parse.py  Mapping analysis
│   ├── synonym_mapping_summary.py  Summary statistics
│   ├── analyze_fungidb_species.py  FungiDB analysis
│   └── config.yaml.template    Configuration template
│
├── plot/                       Plotting modules (29)
│   ├── plot_ipr_*.py          IPR domain scatter plots
│   ├── plot_scenario_barplot.py  Scenario distribution
│   ├── plot_proteinx_comparison.py  ProteinX/pLDDT comparison
│   ├── plot_fungidb_analysis.py  FungiDB analysis plots
│   ├── flexible_api.py        Data-agnostic plotting functions
│   ├── flexible_psauron_plddt.py  Dual metric comparison plots
│   ├── scenarios.py           Scenario helper functions
│   ├── advanced.py            Advanced analysis plots
│   └── ... (22 more plotting modules)
│
├── plots/                      Output directory (active)
│   ├── test_summary_*.png     Generated plots
│   ├── gene_level_*.tsv       Gene-level analysis data
│   └── transcript_level_*.tsv Transcript-level data
│
├── tmp/                        Archive (1.8 GB)
│   ├── pavprot_out_*          Old PAVprot outputs
│   ├── complete_plots_final   Previous plot versions
│   └── ... (archived data)
│
└── docs/                       Documentation & guides
```

## Module Organization

### **src/pavprot.py** - Main Entry Point
- **Purpose**: PAVprot data processing pipeline
- **Features**:
  - GffCompare tracking file parsing
  - Gene/transcript mapping classification
  - DIAMOND BLASTP integration
  - InterProScan domain annotation
  - ProteinX pLDDT integration
  - Psauron score integration
  - Plot generation (via `--plot` flag)
- **Key Arguments**:
  - `--gff-comp` (required for processing)
  - `--gff`, `--prot` (input files)
  - `--run-diamond`, `--run-interproscan` (enable external tools)
  - `--plot` (plot types to generate)
  - `--plot-only` (skip data processing, plot only)
  - `--dataset` (for --plot-only mode)
  - `--list` (show available plots)

### **scripts/run_pipeline.py** - Pipeline Orchestrator
- **Purpose**: High-level PAVprot workflow orchestration
- **Features**:
  - Psauron data integration
  - ProteinX pLDDT enrichment
  - Automatic data detection
  - Flexible output configuration
- **Key Arguments**:
  - `--task psauron` (data integration task)
  - `--dataset` (input directory)
  - `--output` (output directory, defaults to gene_pav/plots)
  - `--list` (show available tasks)

### **plot/** - Plotting Module (29 modules)

#### Core Plotting Functions
- `flexible_api.py` - Data-agnostic plotting with no hard-coded labels
- `flexible_psauron_plddt.py` - Dual metric comparison plots

#### IPR Domain Plots
- `plot_ipr_scatter_by_class.py` - Scatter by class type
- `plot_ipr_loglog_scale.py` - Log-log scale scatter
- `plot_ipr_loglog_class_shapes.py` - Log-log with shapes
- `plot_ipr_quadrants.py` - Quadrant analysis
- `plot_ipr_quadrants_swapped.py` - Swapped quadrant encoding

#### Quality & Comparison Plots
- `plot_proteinx_comparison.py` - pLDDT confidence plots
- `plot_fungidb_analysis.py` - FungiDB-specific analysis
- `plot_scenario_barplot.py` - Scenario distributions

#### Additional Analysis
- `scenarios.py` - Scenario classification
- `advanced.py` - Advanced IPR analysis
- Plus 20 additional specialized plotting modules

### **scripts/** - Utility Scripts (13 modules)

| Script | Purpose |
|--------|---------|
| `run_pipeline.py` | Pipeline orchestration and data integration |
| `parse_interproscan.py` | InterProScan TSV output parsing |
| `bidirectional_best_hits.py` | Bidirectional best hits (BBH) analysis |
| `gsmc.py` | Gene/Scenario Mapping Classification |
| `mapping_multiplicity.py` | Detect 1:N and N:1 mapping relationships |
| `pairwise_align_prot.py` | Protein sequence pairwise alignment |
| `tools_runner.py` | External tool execution wrapper |
| `parse_liftover_extra_copy_number.py` | Copy number variation detection |
| `inconsistent_genes_transcript_IPR_PAV.py` | IPR inconsistency detection |
| `synonym_mapping_parse.py` | Synonym and mapping analysis |
| `synonym_mapping_summary.py` | Summary statistics generation |
| `analyze_fungidb_species.py` | FungiDB species analysis |
| `config.yaml.template` | Configuration template file |

## Biological Scenarios Detected

PAVprot identifies gene relationships through GffCompare classification:

| Scenario | Code | Description |
|----------|------|-------------|
| 1:1 Ortholog | E | Perfect gene correspondence (true orthology) |
| One-to-Many | A | One old gene maps to multiple new genes |
| Many-to-One | B | Multiple old genes map to one new gene |
| Complex One-to-Many | J | One old gene maps to 3+ new genes |
| Cross-Mapping Groups | CDI | Complex cross-species mapping patterns |
| Positional Swap | F | Adjacent gene inversions/swaps |
| Unmapped Old | G | Old genes with no mapping in new annotation |
| Unmapped New | H | New genes with no mapping in old annotation |

## Output Files

### Primary Output Files

| File | Description |
|------|-------------|
| `*_diamond_blastp.tsv` | Main transcript-level mapping output |
| `*_gene_level.tsv` | Gene-level aggregated results |
| `*_diamond_blastp.xlsx` | **Excel workbook** with all results (11 sheets) |
| `*_old_to_multiple_new.tsv` | One-to-many mapping analysis |
| `*_new_to_multiple_old.tsv` | Many-to-one mapping analysis |
| `*_total_ipr_length.tsv` | IPR domain lengths per gene |

### Excel Export Structure (Default: Enabled)

All results are automatically exported to a single Excel workbook with 11 sheets:
- `transcript_level` - Full transcript-level analysis
- `gene_level` - Aggregated gene-level results
- `old_to_multi_new` - One-to-many mapping relationships
- `new_to_multi_old` - Many-to-one mapping relationships
- `old_domain_dist` - Old annotation domain distributions
- `new_domain_dist` - New annotation domain distributions
- `ipr_length` - Combined IPR lengths (with source column)
- `bbh_results` - Bidirectional best hits analysis
- Plus 3 additional analysis sheets

Use `--no-output-excel` to disable Excel export.

### Output Directory Structure

```
gene_pav/plots/
├── test_summary_by_class_type.png              (164 KB)
├── test_summary_loglog_scale.png               (334 KB)
├── test_summary_loglog_scale_class_shapes.png  (369 KB)
├── test_summary_quadrants_gene_level.png       (165 KB)
├── test_summary_quadrants_gene_level_swapped.png (149 KB)
├── gene_level_with_psauron.tsv                 (2.9 MB)
└── transcript_level_with_psauron.tsv           (3.7 MB)
```

## Data Flow

```
Input Files (GFF, FASTA, InterProScan, Tracking)
         ↓
   src/pavprot.py (main processor)
         ↓
   Gene mapping classification & analysis
         ↓
   scripts/run_pipeline.py (integrator)
         ↓
   Data enrichment (Psauron, ProteinX, pLDDT)
         ↓
   plot/ modules (visualization)
         ↓
   gene_pav/plots/ (final output)
```

## Plotting Architecture

### Legend Positioning

All test* plots have **legends positioned INSIDE** the plot area using:
- Primary legend: `loc='upper left'`, `bbox_to_anchor=(0.05, 0.95)`
- Secondary legend: `loc='upper left'`, `bbox_to_anchor=(0.05, 0.50)`
- Semi-transparent background: `framealpha=0.95` for visibility

### Flexible API

The plotting system uses a data-agnostic API with NO hard-coded labels:
- All labels provided as positional arguments
- Same functions work for any comparable datasets
- Enables reuse for Ref/Qry, old/new, or any data source terminology
- Consistent visual styling across all plots

### Import Architecture

#### Relative Imports (Package-internal)
```python
# In plot/__init__.py - standard package imports
from .plot_ipr_loglog_scale import generate_ipr_loglog_scale
from .flexible_api import scatter_comparison_plot
```

#### Absolute Imports (External)
```bash
# From project root or other locations
python gene_pav/src/pavprot.py --list
python gene_pav/scripts/run_pipeline.py --task psauron
```

## Key Features

### ✓ Flexible Plotting API
- **No Hard-Coded Labels**: All labels provided as positional arguments
- **Data-Agnostic**: Same functions work for any comparable datasets
- **Consistent**: Legends inside plots with semi-transparent background

### ✓ Comprehensive Analysis
- Gene/transcript mapping classification
- Presence/absence variation detection
- Multi-mapping relationship analysis
- Quality score integration

### ✓ Integrated External Tools
- DIAMOND BLASTP protein alignment
- InterProScan domain annotation
- ProteinX pLDDT structure confidence
- Psauron protein similarity scoring

### ✓ Clean Organization
- Main script in `src/`
- Utilities in `scripts/`
- Plotting in `plot/`
- Output to `plots/`
- Archive in `tmp/`

## Configuration

### Default Output Directory
Default: `gene_pav/plots/`

### Override with:
```bash
# Using src/pavprot.py
python gene_pav/src/pavprot.py --output-dir /custom/path

# Using scripts/run_pipeline.py
python gene_pav/scripts/run_pipeline.py --output /custom/path
```

## Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/gene_pav.git
cd gene_pav

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python gene_pav/src/pavprot.py --help
```

## Requirements

### Python Dependencies
- Python 3.8+
- pandas >= 1.3.0
- numpy >= 1.21.0
- matplotlib >= 3.4.0
- seaborn >= 0.11.0
- scipy >= 1.7.0
- BioPython >= 1.79 (for protein alignment)
- pyyaml >= 5.4.0 (for configuration)
- openpyxl >= 3.0.0 (for Excel export)

### External Tools (Optional)
- **DIAMOND** - Fast sequence alignment
- **InterProScan** - Protein domain detection
- **gffcompare** - GFF comparison
- **Liftoff** - Annotation liftover
- **BUSCO** - Completeness assessment

## Project-Specific Scripts

The `scripts/` directory contains **project-specific workflow examples** built on top of PAVprot. These serve as templates for real analyses:

### Available Scripts

| Script | Purpose | Customization |
|--------|---------|---------------|
| `run_pipeline.py` | Master workflow orchestrator | Use `--config` flag or edit CONFIG dict |
| `run_emckmnje1_analysis.py` | Filtered analysis wrapper | Update input/output paths |
| `analyze_fungidb_species.py` | FungiDB species-level analysis | Update data file paths |
| `plot_oldvsnew_psauron_plddt.py` | Annotation comparison plots | Update input TSV paths |
| `plot_ipr_1to1_comparison.py` | IPR domain comparison for 1:1 orthologs | Update input/output paths |
| `plot_psauron_distribution.py` | Psauron score distribution plots | Update input/output paths |

### Configuration

**Option 1: Use config.yaml (Recommended)**
```bash
# Copy template and edit
cp gene_pav/scripts/config.yaml.template config.yaml
nano config.yaml  # or your preferred editor

# Run with config file
python gene_pav/scripts/run_pipeline.py --config config.yaml --all
```

**Option 2: Edit CONFIG dict directly**
```python
# For quick one-off runs, edit CONFIG dict at top of run_pipeline.py
CONFIG = {
    "gene_pav_dir": Path(__file__).parent,
    "output_dir": Path(__file__).parent / "pipeline_output",
    "psauron_ref": Path("/your/path/to/psauron/ref_all.csv"),
    # ... etc
}
```

### Available Tasks

| Task | Description |
|------|-------------|
| `plots` | Generate all plots |
| `psauron` | Psauron quality score analysis |
| `proteinx` | ProteinX/pLDDT analysis |
| `fungidb` | FungiDB comparative analysis |
| `ipr` | InterPro domain analysis |
| `scenarios` | Scenario classification analysis |

### Usage Examples

```bash
# Run all tasks
python gene_pav/scripts/run_pipeline.py --config config.yaml --all

# Run specific task
python gene_pav/scripts/run_pipeline.py --config config.yaml --task plots

# List available tasks
python gene_pav/scripts/run_pipeline.py --list

# Dry run (show what would be done)
python gene_pav/scripts/run_pipeline.py --config config.yaml --all --dry-run
```

## Testing

### Test Data

The `test/` directory contains minimal test data for validating PAVprot functionality:

**Test Scenario**: Single GFF + Single InterProScan + gffcompare (most common use case)

### Directory Structure

```
gene_pav/test/
├── input/
│   ├── test_interproscan.tsv        # InterProScan TSV output (10 entries)
│   ├── gffcompare.tracking          # GFFcompare tracking file
│   └── gff_feature_table.gff3       # Reference GFF3 annotation
└── output/
    ├── test_interproscan_total_ipr_length.tsv
    ├── test_interproscan_domain_distribution.tsv
    └── synonym_mapping_liftover_gffcomp_test_demo_e_m.tsv
```

### Running Tests

```bash
# From the repository root directory
python gene_pav/src/pavprot.py \
  --gff-comp gene_pav/test/input/gffcompare.tracking \
  --gff gene_pav/test/input/gff_feature_table.gff3 \
  --interproscan-out gene_pav/test/input/test_interproscan.tsv \
  --class-code e m \
  --output-prefix test_demo
```

### Expected Test Outputs

1. **Total IPR Length File** - Total IPR lengths per gene
2. **Domain Distribution File** - Domain statistics with column indicators
3. **PAVprot Output** - Standard output with InterProScan columns

Output files are saved to `pavprot_out/` directory (not in test/output).

## Troubleshooting

### Import Errors
- All relative imports use dot notation (`.module_name`)
- Valid from anywhere via `python gene_pav/src/pavprot.py`
- Scripts path added automatically in `src/pavprot.py`

### Plot Generation
- Legends positioned inside plots with `bbox_to_anchor` coordinates
- Output defaults to `gene_pav/plots/`
- Check for missing data columns with `--plot-only` mode
- Use `--list` to see all available plot types

### Data Integration
- Psauron data auto-detected in `pavprot_out_*/psauron/`
- ProteinX data auto-detected in `pavprot_out_*/proteinx/`
- Use `--dataset` flag to specify custom data location
- Run `run_pipeline.py --list` to see available tasks

## Documentation

- **ARCHITECTURE.md** - Module connectivity and data flow
- **SCENARIOS.md** - Biological scenario reference
- **OUTPUT_FORMAT.md** - Column descriptions
- **IMPLEMENTATION_ROADMAP.md** - Future improvements
- Inline code documentation in each module

## License

See LICENSE file for details.

---

**Comprehensive source of truth for PAVprot pipeline. For detailed information on specific modules, see the individual `.md` files in the docs/ directory.**
