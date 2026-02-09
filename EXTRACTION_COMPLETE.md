# Plot Code Extraction Complete ✓

## Summary
All 18 plotting tasks have been successfully extracted from `run_pipeline.py` and moved to `plot/extracted_tasks/` as standalone functions.

## What Was Extracted

### All 18 Plot Tasks → plot/extracted_tasks/

1. ✓ `task_1_ipr_scatter.py` - IPR scatter plot by class type
2. ✓ `task_2_loglog_scale.py` - Log-log scale plot with mapping type shapes
3. ✓ `task_2b_loglog_class_shapes.py` - Log-log scale with class type shapes
4. ✓ `task_3_quadrants.py` - Quadrant analysis plot
5. ✓ `task_3b_quadrants_swapped.py` - Quadrant analysis (swapped)
6. ✓ `task_4_scenario_barplot.py` - Scenario bar plot
7. ✓ `task_5_proteinx.py` - ProteinX/pLDDT comparison
8. ✓ `task_7_psauron_plots.py` - Psauron score plots
9. ✓ `task_8_fungidb_analysis.py` - FungiDB transcript analysis
10. ✓ `task_9_ipr_scatter_by_class.py` - IPR scatter by class (duplicate)
11. ✓ `task_10_ipr_loglog_by_mapping.py` - Log-log by mapping (duplicate)
12. ✓ `task_11_ipr_quadrant_analysis.py` - Quadrant analysis (duplicate)
13. ✓ `task_12_class_code_distribution.py` - Class code distribution (duplicate)
14. ✓ `task_13_scenario_detailed.py` - Detailed scenario (duplicate)
15. ✓ `task_14_1to1_ipr_plots.py` - 1:1 IPR comparison (duplicate)
16. ✓ `task_15_psauron_dist_by_mapping_and_class.py` - Psauron distribution (duplicate)
17. ✓ `task_16_psauron_scatter.py` - Psauron scatter (duplicate)
18. ✓ `task_17_scenario_distribution.py` - Scenario distribution (duplicate)

## Extraction Format

### Before (Class Method in run_pipeline.py)
```python
class PipelineRunner:
    def task_1_ipr_scatter(self) -> Optional[Path]:
        if self.gene_df is None:
            return None
        df = self.gene_df.copy()
        output_path = self.output_dir / "plot.png"
```

### After (Standalone Function in plot/extracted_tasks/)
```python
def generate_1_ipr_scatter(gene_df: pd.DataFrame = None,
                          transcript_df: pd.DataFrame = None,
                          output_dir: Path = None,
                          config: dict = None,
                          figure_dpi: int = 150) -> Optional[Path]:
    if gene_df is None:
        return None
    df = gene_df.copy()
    output_path = output_dir / "plot.png"
```

## Key Changes

✓ **Removed `self` references**: All `self.X` converted to function parameters
✓ **Standalone functions**: No longer class methods
✓ **Proper imports**: All dependencies imported at module level
✓ **Configurable**: Parameters for gene_df, output_dir, figure_dpi, etc.
✓ **Documentation**: Each file includes source and purpose notes
✓ **Helper functions**: `mapping_type_to_colon()` included in each file

## File Structure

```
plot/extracted_tasks/
├── task_1_ipr_scatter.py
├── task_2_loglog_scale.py
├── task_2b_loglog_class_shapes.py
├── task_3_quadrants.py
├── task_3b_quadrants_swapped.py
├── task_4_scenario_barplot.py
├── task_5_proteinx.py
├── task_7_psauron_plots.py
├── task_8_fungidb_analysis.py
├── task_9_ipr_scatter_by_class.py
├── task_10_ipr_loglog_by_mapping.py
├── task_11_ipr_quadrant_analysis.py
├── task_12_class_code_distribution.py
├── task_13_scenario_detailed.py
├── task_14_1to1_ipr_plots.py
├── task_15_psauron_dist_by_mapping_and_class.py
├── task_16_psauron_scatter.py
└── task_17_scenario_distribution.py
```

## Status

| Component | Status |
|-----------|--------|
| All tasks extracted | ✓ Complete |
| All standalone functions | ✓ Complete |
| All class methods removed from run_pipeline.py | ✓ Complete |
| Imports cleaned up | ✓ Complete |
| Self references removed | ✓ Complete |
| Helper functions included | ✓ Complete |

## Next Steps

### For Duplicate Tasks (Use plot/ module instead)
- task_7_psauron_plots → Use `plot/plot_oldvsnew_psauron_plddt.py`
- task_9_ipr_scatter_by_class → Use `plot/advanced.py`
- task_10_ipr_loglog_by_mapping → Use `plot/advanced.py`
- task_11_ipr_quadrant_analysis → Use `plot/advanced.py`
- task_12_class_code_distribution → Use `plot/scenarios.py`
- task_13_scenario_detailed → Use `plot/advanced.py`
- task_14_1to1_ipr_plots → Use `plot/plot_ipr_1to1_comparison.py`
- task_15_psauron_dist_by_mapping_and_class → Use `plot/plot_oldvsnew_psauron_plddt.py`
- task_16_psauron_scatter → Use `plot/plot_oldvsnew_psauron_plddt.py`
- task_17_scenario_distribution → Use `plot/scenarios.py`

### For Unique Tasks
- Consider integrating into appropriate plot module files
- Or keep as reference implementations in extracted_tasks/

## Usage Examples

### From Python
```python
from gene_pav.plot.extracted_tasks.task_1_ipr_scatter import generate_1_ipr_scatter
import pandas as pd
from pathlib import Path

gene_df = pd.read_csv('gene_level.tsv', sep='\t')
output_path = generate_1_ipr_scatter(
    gene_df=gene_df,
    output_dir=Path('output'),
    figure_dpi=150
)
```

### From Command Line
```bash
python plot/extracted_tasks/task_1_ipr_scatter.py gene_level.tsv output_dir
```

---
**Date:** 2026-02-09
**Status:** EXTRACTION COMPLETE ✓
**Total Tasks Extracted:** 18/18
