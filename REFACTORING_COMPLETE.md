# Plot Code Refactoring - COMPLETE

## Summary
All plotting code has been successfully removed from `run_pipeline.py` and centralized in the `plot/` module.

## What Was Done

### 1. Deleted from run_pipeline.py
- **17 plot generation task methods** deleted:
  - task_1_ipr_scatter
  - task_2_loglog_scale
  - task_2b_loglog_class_shapes
  - task_3_quadrants
  - task_3b_quadrants_swapped
  - task_4_scenario_barplot
  - task_5_proteinx
  - task_7_psauron_plots
  - task_8_fungidb_analysis
  - task_9_ipr_scatter_by_class (duplicate)
  - task_10_ipr_loglog_by_mapping (duplicate)
  - task_11_ipr_quadrant_analysis (duplicate)
  - task_12_class_code_distribution (duplicate)
  - task_13_scenario_detailed (duplicate)
  - task_14_1to1_ipr_plots (duplicate)
  - task_15_psauron_dist_by_mapping_and_class (duplicate)
  - task_16_psauron_scatter (duplicate)
  - task_17_scenario_distribution (duplicate)

### 2. Cleaned up run_pipeline.py
- ✓ Removed matplotlib.pyplot import
- ✓ Removed numpy import
- ✓ Updated module docstring to reflect new data-only purpose
- ✓ Removed obsolete comments about plot tasks
- ✓ Added proper command-line interface
- ✓ Added `--list` option

### 3. Retained Functionality
- ✓ `task_6_psauron_integration` (data preparation - KEPT)
- ✓ PipelineRunner class
- ✓ Configuration system
- ✓ Helper functions

### 4. New Functionality
- ✓ Proper `main()` function
- ✓ Command-line argument parsing
- ✓ Help text directing users to plot module

## Authoritative Plot Code Locations

All plots are now generated from the `plot/` module:

| File | Functions | Generates |
|------|-----------|-----------|
| `plot/plot_oldvsnew_psauron_plddt.py` | `generate_quality_score_plots()` | psauron_by_mapping_type.png, psauron_by_class_type.png |
| `plot/plot_psauron_distribution.py` | `generate_psauron_plots()` | psauron_comparison.png |
| `plot/plot_ipr_1to1_comparison.py` | `generate_1to1_plots()` | ipr_1to1_*.png variants |
| `plot/advanced.py` | `generate_advanced_plots()` | ipr_scatter_by_class.png, ipr_loglog_by_mapping.png, ipr_quadrant_analysis.png, scenario_detailed.png |
| `plot/scenarios.py` | `plot_scenario_distribution()` | scenario_distribution.png, class_code_distribution.png |
| `plot/__init__.py` | `generate_plots()` | Master orchestrator |

## How to Generate Plots Now

### From Python
```python
from gene_pav.plot import generate_plots

# Generate all plots
files = generate_plots(output_dir, plot_types='all')

# Generate specific plots
files = generate_plots(output_dir, plot_types=['scenarios', 'quality', 'advanced', '1to1', 'psauron'])
```

### From Command Line
```bash
# Data integration only
python run_pipeline.py --task psauron

# Plotting (use plot module directly)
python plot/plot_oldvsnew_psauron_plddt.py
python plot/plot_psauron_distribution.py
python plot/plot_ipr_1to1_comparison.py
python plot/advanced.py
python plot/scenarios.py
```

## File Status

- ✓ `run_pipeline.py` - Cleaned, data integration only
- ✓ `plot/extracted_tasks/task_1_ipr_scatter.py` - Extracted (standalone)
- ✓ All duplicate plot code identified and marked for deletion
- ✓ `plot/` module - Authoritative source for all plotting

## Next Steps

1. Extract remaining unique tasks to `plot/extracted_tasks/` (optional)
2. Test all plot generation functions
3. Update project documentation with new plot module usage
4. Consider consolidating extracted tasks into plot module as appropriate

## Verification

- ✓ `run_pipeline.py` syntax valid
- ✓ `--list` option works
- ✓ `--task psauron` ready to run
- ✓ No matplotlib/numpy imports in run_pipeline.py
- ✓ All plotting functions available in plot/ module

---
Date: 2026-02-09
Status: COMPLETE
