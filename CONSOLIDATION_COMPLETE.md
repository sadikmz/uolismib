# Plot Code Consolidation - COMPLETE ✓

## Architecture

### THREE-LAYER ORGANIZATION

```
plot/
├── *.py (AUTHORITATIVE - 5 modules)
│   ├── plot_oldvsnew_psauron_plddt.py      (Psauron: mapping_type, class_type, scatter)
│   ├── plot_psauron_distribution.py         (Psauron distribution comparison)
│   ├── plot_ipr_1to1_comparison.py          (IPR 1:1 ortholog pairs)
│   ├── advanced.py                          (IPR advanced: log-log, quadrant, scenario)
│   ├── scenarios.py                         (Scenario & class code distribution)
│   └── __init__.py                          (Master orchestrator)
│
└── extracted_tasks/ (REFERENCE/ARCHIVAL - 18 standalone functions)
    ├── UNIQUE (9 tasks - new functionality)
    │   ├── task_1_ipr_scatter.py
    │   ├── task_2_loglog_scale.py
    │   ├── task_2b_loglog_class_shapes.py
    │   ├── task_3_quadrants.py
    │   ├── task_3b_quadrants_swapped.py
    │   ├── task_4_scenario_barplot.py
    │   ├── task_5_proteinx.py
    │   ├── task_8_fungidb_analysis.py
    │   └── task_15_psauron_dist_by_mapping_and_class.py
    │
    └── DUPLICATES (9 tasks - reference only, use plot/*.py instead)
        ├── task_7_psauron_plots.py           → Use plot_oldvsnew_psauron_plddt.py
        ├── task_9_ipr_scatter_by_class.py    → Use advanced.py
        ├── task_10_ipr_loglog_by_mapping.py  → Use advanced.py
        ├── task_11_ipr_quadrant_analysis.py  → Use advanced.py
        ├── task_12_class_code_distribution.py → Use scenarios.py
        ├── task_13_scenario_detailed.py      → Use advanced.py
        ├── task_14_1to1_ipr_plots.py         → Use plot_ipr_1to1_comparison.py
        ├── task_16_psauron_scatter.py        → Use plot_oldvsnew_psauron_plddt.py
        └── task_17_scenario_distribution.py  → Use scenarios.py
```

## Priority Hierarchy

### 1. AUTHORITATIVE (Use These)
**plot/*.py modules** have priority. These are the definitive implementations:
- `plot_oldvsnew_psauron_plddt.py` - Psauron quality score scatter plots
- `plot_psauron_distribution.py` - Psauron distribution histograms
- `plot_ipr_1to1_comparison.py` - IPR domain comparison for 1:1 orthologs
- `advanced.py` - Advanced IPR analysis (log-log, quadrant analysis)
- `scenarios.py` - Scenario distributions and class codes

### 2. REFERENCE (extracted_tasks/)
All 18 extracted standalone functions for:
- Archival/historical reference
- Understanding original implementations
- Integration candidates (for unique ones)

### 3. DEPRECATED (run_pipeline.py - EMPTY OF PLOTS)
- Only `task_6_psauron_integration` remains
- No plotting code
- No matplotlib/numpy imports

## Figure Generation Map

### AUTHORITATIVE (plot/*.py)

| Module | Function | Outputs |
|--------|----------|---------|
| plot_oldvsnew_psauron_plddt.py | generate_quality_score_plots() | psauron_by_mapping_type.png, psauron_by_class_type.png, psauron_scatter.png |
| plot_psauron_distribution.py | generate_psauron_plots() | psauron_comparison.png |
| plot_ipr_1to1_comparison.py | generate_1to1_plots() | ipr_1to1_by_class_type.png, ipr_1to1_no_class.png, ipr_1to1_*_log.png |
| advanced.py | generate_advanced_plots() | ipr_scatter_by_class.png, ipr_loglog_by_mapping.png, ipr_quadrant_analysis.png, scenario_detailed.png |
| scenarios.py | plot_scenario_distribution() | scenario_distribution.png, class_code_distribution.png |

### REFERENCE (extracted_tasks/) - SAME OUTPUTS

| Duplicate Task | Maps To |
|---|---|
| task_7_psauron_plots.py | plot_oldvsnew_psauron_plddt.py |
| task_9_ipr_scatter_by_class.py | advanced.py |
| task_10_ipr_loglog_by_mapping.py | advanced.py |
| task_11_ipr_quadrant_analysis.py | advanced.py |
| task_12_class_code_distribution.py | scenarios.py |
| task_13_scenario_detailed.py | advanced.py |
| task_14_1to1_ipr_plots.py | plot_ipr_1to1_comparison.py |
| task_16_psauron_scatter.py | plot_oldvsnew_psauron_plddt.py |
| task_17_scenario_distribution.py | scenarios.py |

### UNIQUE FUNCTIONS (extracted_tasks/) - NEW FUNCTIONALITY

| Task | Output | Status |
|------|--------|--------|
| task_1_ipr_scatter.py | test_summary_by_class_type.png | Ready for plot/ integration |
| task_2_loglog_scale.py | test_summary_loglog_scale.png | Ready for plot/ integration |
| task_2b_loglog_class_shapes.py | test_summary_loglog_scale_class_shapes.png | Ready for plot/ integration |
| task_3_quadrants.py | test_summary_quadrants_gene_level.png | Ready for plot/ integration |
| task_3b_quadrants_swapped.py | test_summary_quadrants_gene_level_swapped.png | Ready for plot/ integration |
| task_4_scenario_barplot.py | scenario_barplot.png | Ready for plot/ integration |
| task_5_proteinx.py | proteinx_comparison.png | Ready for plot/ integration |
| task_8_fungidb_analysis.py | gene_counts_by_genus.png, exons_per_*.png | Ready for plot/ integration |
| task_15_psauron_dist_by_mapping_and_class.py | psauron_distribution_by_mapping_and_class.png | Ready for plot/ integration |

## Usage Recommendations

### For Production Use
```python
from gene_pav.plot import generate_plots

# Generate all plots using authoritative modules
files = generate_plots(
    output_dir,
    plot_types=['scenarios', 'quality', 'advanced', '1to1', 'psauron']
)
```

### For Reference/Integration
```python
# Review unique extracted tasks for integration into plot/
from gene_pav.plot.extracted_tasks.task_1_ipr_scatter import generate_1_ipr_scatter

# Or review duplicate implementations for comparison
from gene_pav.plot.extracted_tasks.task_7_psauron_plots import generate_psauron_plots  # Compare with authoritative version
```

## Summary Table

| Aspect | Authoritative | Extracted (Duplicates) | Extracted (Unique) |
|--------|---|---|---|
| Location | `plot/*.py` | `plot/extracted_tasks/` | `plot/extracted_tasks/` |
| Purpose | Production | Reference only | Reference + Integration |
| Count | 5 modules | 9 functions | 9 functions |
| Maintenance | Active | Historical | For future integration |
| Priority | ✓ USE THIS | Use authoritative instead | Consider for integration |

## Next Steps

### Immediate
- ✓ All plotting code extracted from run_pipeline.py
- ✓ Authoritative plot modules active in plot/
- ✓ All 18 extracted tasks available for reference in extracted_tasks/

### Optional Future
1. Integrate unique extracted tasks into appropriate plot/ modules
2. Create unified plot generation functions for test_summary_* plots
3. Add FungiDB analysis plots to plot module

---

**Date:** 2026-02-09
**Status:** CONSOLIDATION COMPLETE ✓

**Key Points:**
- ✓ plot/*.py = Authoritative (has priority)
- ✓ extracted_tasks/ = Complete reference archive (9 unique + 9 duplicates)
- ✓ run_pipeline.py = Data integration only
- ✓ All plotting centralized in plot/ module
