# PAVprot Plotting Consolidation - Complete ✓

## Overview

All PAVprot plotting functionality has been consolidated into a unified, well-organized module with clear hierarchy and comprehensive documentation.

**Status:** ✓ COMPLETE (2026-02-09)
- 14 authoritative plot modules
- 9 reference duplicates (archival)
- 1 unified orchestrator interface
- Full CLI support

---

## Architecture

### Three-Layer Organization

```
pavprot/                              (DATA PROCESSING)
├── pavprot.py                        Main PAVprot class
├── parse_interproscan.py
├── mapping_multiplicity.py
├── bidirectional_best_hits.py
├── pairwise_align_prot.py
└── gsmc.py                           Gene sequence mapping classification

plot/                                 (PLOTTING - AUTHORITATIVE)
├── __init__.py                       Master orchestrator: generate_plots()
├── config.py                         Configuration & styling
├── utils.py                          Data loading utilities
│
├── Core Modules (5):
│   ├── plot_oldvsnew_psauron_plddt.py        Quality score scatter plots
│   ├── plot_psauron_distribution.py          Psauron distribution histograms
│   ├── plot_ipr_1to1_comparison.py           IPR 1:1 ortholog comparison
│   ├── advanced.py                           Advanced IPR (log-log, quadrant)
│   └── scenarios.py                          Scenario distributions
│
├── New Integrated Modules (9):
│   ├── plot_ipr_scatter_by_class.py          IPR scatter by class type
│   ├── plot_ipr_loglog_scale.py              Log-log scale plots
│   ├── plot_ipr_loglog_class_shapes.py       Log-log with class shapes
│   ├── plot_ipr_quadrants.py                 Quadrant analysis
│   ├── plot_ipr_quadrants_swapped.py         Quadrants (swapped)
│   ├── plot_scenario_barplot.py              Scenario bar plot
│   ├── plot_proteinx_comparison.py           ProteinX/pLDDT comparison
│   ├── plot_fungidb_analysis.py              FungiDB analysis
│   └── plot_psauron_by_mapping_class.py      Psauron by mapping/class
│
└── extracted_tasks/                  (REFERENCE ONLY - 9 duplicates)
    ├── task_7_psauron_plots.py
    ├── task_9_ipr_scatter_by_class.py
    ├── task_10_ipr_loglog_by_mapping.py
    ├── task_11_ipr_quadrant_analysis.py
    ├── task_12_class_code_distribution.py
    ├── task_13_scenario_detailed.py
    ├── task_14_1to1_ipr_plots.py
    ├── task_16_psauron_scatter.py
    └── task_17_scenario_distribution.py

pavprot_complete.py                   (UNIFIED ORCHESTRATOR)
   └── Complete workflow: data + plotting

run_pipeline.py                       (DATA PREPARATION ONLY)
   └── Psauron integration task
```

---

## Priority Hierarchy

### 1. ✓ USE THESE: Authoritative Plot Modules (`plot/*.py`)
14 production-ready modules with clear, focused purposes:

**Core Modules (5):**
- `plot_oldvsnew_psauron_plddt.py` - Quality score scatter plots (new vs old annotation)
- `plot_psauron_distribution.py` - Psauron distribution histograms
- `plot_ipr_1to1_comparison.py` - IPR domain comparison for 1:1 ortholog pairs
- `advanced.py` - Advanced IPR analysis (log-log scale, quadrant analysis)
- `scenarios.py` - Scenario and class code distribution plots

**New Integrated Modules (9):**
- `plot_ipr_scatter_by_class.py` - Generates: test_summary_by_class_type.png
- `plot_ipr_loglog_scale.py` - Generates: test_summary_loglog_scale.png
- `plot_ipr_loglog_class_shapes.py` - Generates: test_summary_loglog_scale_class_shapes.png
- `plot_ipr_quadrants.py` - Generates: test_summary_quadrants_gene_level.png
- `plot_ipr_quadrants_swapped.py` - Generates: test_summary_quadrants_gene_level_swapped.png
- `plot_scenario_barplot.py` - Generates: scenario_barplot.png
- `plot_proteinx_comparison.py` - Generates: proteinx_comparison.png
- `plot_fungidb_analysis.py` - Generates: FungiDB analysis plots
- `plot_psauron_by_mapping_class.py` - Generates: psauron_distribution_by_mapping_and_class.png

### 2. REFERENCE ONLY: Duplicate Implementations (`plot/extracted_tasks/`)
9 duplicate reference files for archival/comparison. Use authoritative versions instead.

### 3. DEPRECATED: Run Pipeline (`run_pipeline.py`)
Data preparation only. No plotting code.
- Only `task_6_psauron_integration` remains
- Use for data enrichment, not plotting

---

## Complete API Reference

### Import Individual Plot Functions

```python
from gene_pav.plot import (
    # Core functions
    generate_quality_score_plots,
    generate_psauron_plots,
    generate_1to1_plots,

    # New integrated functions
    generate_ipr_scatter_by_class,
    generate_ipr_loglog_scale,
    generate_ipr_loglog_class_shapes,
    generate_ipr_quadrants,
    generate_ipr_quadrants_swapped,
    generate_scenario_barplot,
    generate_proteinx_comparison,
    generate_fungidb_analysis,
    generate_psauron_by_mapping_class,
)

# Use individual functions
import pandas as pd
from pathlib import Path

gene_df = pd.read_csv('gene_level.tsv', sep='\t')
output_dir = Path('plots/')

# Generate IPR scatter by class
plot_path = generate_ipr_scatter_by_class(
    gene_df=gene_df,
    output_dir=output_dir,
    figure_dpi=150
)
```

### Use Master Orchestrator

```python
from gene_pav.plot import generate_plots

# Generate all plots
generated_files = generate_plots(
    output_dir='results/',
    plot_types=['scenarios', 'ipr', 'advanced', '1to1', 'psauron', 'quality'],
    gene_level_file='gene_level.tsv',
    figure_dpi=150
)

# Available plot types:
# - scenarios: Scenario distribution plots
# - ipr: IPR scatter by class type
# - advanced: Advanced IPR analysis (log-log, quadrant, detailed)
# - 1to1: IPR 1:1 ortholog pair comparison
# - psauron: Psauron score distributions
# - quality: Quality scores (new vs old annotation)
# - all: All available plots
```

---

## CLI Usage

### Complete Workflow (Data + Plotting)

```bash
# Full pipeline
python pavprot_complete.py --gff-comp tracking.txt \
  --gff old.gff3,new.gff3 \
  --prot old.faa,new.faa \
  --run-diamond \
  --full-workflow
```

### Data Processing Only

```bash
# Data preparation
python pavprot_complete.py --gff-comp tracking.txt \
  --gff old.gff3,new.gff3 \
  --prot old.faa,new.faa \
  --run-diamond \
  --data-only

# Output: pavprot_out/ directory
```

### Plotting Only

```bash
# All plots
python pavprot_complete.py --plot-only \
  --dataset pavprot_out/ \
  --plot-types all

# Specific plots
python pavprot_complete.py --plot-only \
  --dataset pavprot_out/ \
  --plot-types scenarios,ipr,advanced,1to1

# List available plot types
python pavprot_complete.py --list
```

---

## Function Signature Reference

All plot functions follow a consistent signature:

```python
def generate_[plot_name](
    gene_df: pd.DataFrame = None,           # Gene-level data
    transcript_df: pd.DataFrame = None,     # Transcript-level data (optional)
    output_dir: Path = None,                # Output directory for plots
    config: dict = None,                    # Configuration dict (optional)
    figure_dpi: int = 150                   # Figure DPI (default: 150)
) -> Optional[Path]:
    """
    Generate [plot description].

    Returns:
        Path to output file, or None if skipped
    """
```

---

## Plot Output Mapping

| Plot Module | Function | Output Files |
|---|---|---|
| plot_oldvsnew_psauron_plddt | generate_quality_score_plots() | psauron_by_mapping_type.png, psauron_by_class_type.png, psauron_scatter.png |
| plot_psauron_distribution | generate_psauron_plots() | psauron_comparison.png |
| plot_ipr_1to1_comparison | generate_1to1_plots() | ipr_1to1_by_class_type.png, ipr_1to1_no_class.png, ipr_1to1_*_log.png |
| plot_ipr_scatter_by_class | generate_ipr_scatter_by_class() | test_summary_by_class_type.png |
| plot_ipr_loglog_scale | generate_ipr_loglog_scale() | test_summary_loglog_scale.png |
| plot_ipr_loglog_class_shapes | generate_ipr_loglog_class_shapes() | test_summary_loglog_scale_class_shapes.png |
| plot_ipr_quadrants | generate_ipr_quadrants() | test_summary_quadrants_gene_level.png |
| plot_ipr_quadrants_swapped | generate_ipr_quadrants_swapped() | test_summary_quadrants_gene_level_swapped.png |
| plot_scenario_barplot | generate_scenario_barplot() | scenario_barplot.png |
| plot_proteinx_comparison | generate_proteinx_comparison() | proteinx_comparison.png |
| plot_fungidb_analysis | generate_fungidb_analysis() | gene_counts_by_genus.png, exons_per_*.png |
| plot_psauron_by_mapping_class | generate_psauron_by_mapping_class() | psauron_distribution_by_mapping_and_class.png |
| advanced.py | generate_advanced_plots() | ipr_scatter_by_class.png, ipr_loglog_by_mapping.png, ipr_quadrant_analysis.png, scenario_detailed.png |
| scenarios.py | plot_scenario_distribution() | scenario_distribution.png, class_code_distribution.png |

---

## Integration with PAVprot Data Processing

The plotting module is independent of data processing but designed to work seamlessly:

```python
# Complete workflow example
import pavprot
from gene_pav.plot import generate_plots

# 1. Process PAVprot output
pav = pavprot.PAVprot()
# ... data processing ...

# 2. Load enriched output
import pandas as pd
gene_df = pd.read_csv('pavprot_out/gene_level_with_psauron.tsv', sep='\t')

# 3. Generate all visualizations
plots = generate_plots(
    output_dir='results/',
    plot_types='all',
    gene_level_file='pavprot_out/gene_level_with_psauron.tsv'
)

print(f"Generated {len(plots)} plots in results/plots/")
```

---

## Migration Guide

### From Old Structure

**Before (scattered plotting code):**
```python
from run_pipeline import PipelineRunner
runner = PipelineRunner(config)
runner.task_1_ipr_scatter()
runner.task_2_loglog_scale()
```

**After (consolidated plotting):**
```python
from gene_pav.plot import (
    generate_ipr_scatter_by_class,
    generate_ipr_loglog_scale,
    generate_plots  # Or use master orchestrator
)

# Option 1: Individual functions
generate_ipr_scatter_by_class(gene_df=df, output_dir=Path('plots'))
generate_ipr_loglog_scale(gene_df=df, output_dir=Path('plots'))

# Option 2: Master orchestrator
generate_plots('plots', plot_types=['ipr', 'advanced'])
```

---

## Status Summary

| Component | Status | Count | Location |
|-----------|--------|-------|----------|
| Authoritative plot modules | ✓ Complete | 14 | plot/*.py |
| New integrated modules | ✓ Complete | 9 | plot/plot_*.py |
| Reference duplicates | ✓ Preserved | 9 | plot/extracted_tasks/ |
| Master orchestrator | ✓ Complete | 1 | plot/__init__.py |
| Unified CLI wrapper | ✓ Complete | 1 | pavprot_complete.py |
| Data integration pipeline | ✓ Complete | 1 | run_pipeline.py |
| Documentation | ✓ Complete | - | This file |

---

## Next Steps

### For Users

1. **Install/Setup:** Ensure plot module is properly installed
2. **Quick Start:** Use `pavprot_complete.py --list` to see available plots
3. **Generate Plots:** Run `pavprot_complete.py --plot-only --plot-types all`
4. **Integrate:** Import from `gene_pav.plot` in your scripts

### For Developers

1. **Add New Plots:** Create `plot_[name].py` following the established pattern
2. **Register Plots:** Import and expose in `plot/__init__.py`
3. **Update Documentation:** Add to this file's mapping table
4. **Test:** Verify with sample data in `plot_out/`

---

## Troubleshooting

### Missing Plots

**Issue:** "Module not found" when importing plot functions
- **Solution:** Ensure `plot/` directory is in Python path or installed properly

### Data Not Found

**Issue:** "No PAVprot output files found"
- **Solution:** Check that gene-level or transcript-level TSV files exist in dataset directory
- Look for: `*_gene_level.tsv`, `*_transcript_level.tsv`, `*_with_psauron.tsv`

### Figure Quality

**Issue:** Plots look pixelated or low-resolution
- **Solution:** Increase `figure_dpi` parameter (default: 150, try 300 for print-quality)

---

## References

- PAVprot Documentation: See `pavprot.py` module docstring
- Plot Configuration: See `plot/config.py` for styling options
- Data Utilities: See `plot/utils.py` for data loading functions

---

**Date:** 2026-02-09
**Status:** CONSOLIDATION COMPLETE ✓

**Key Achievements:**
- ✓ All 18 plotting tasks extracted from run_pipeline.py
- ✓ 9 unique tasks integrated as authoritative modules
- ✓ 9 duplicate tasks preserved as references
- ✓ Master orchestrator API created
- ✓ Unified CLI interface provided
- ✓ Complete documentation generated
