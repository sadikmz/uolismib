# Recommendations: Scripts to Combine or Split

> **Date:** 2026-01-19
> **Task:** Suggest scripts to be combined or split

---

## Executive Summary

| Action | Scripts | Rationale |
|--------|---------|-----------|
| **COMBINE** | 4 plot files → `plot/utils.py` | Duplicated `load_data()` function |
| **COMBINE** | `synonym_mapping_*.py` | Related functionality, one is broken |
| **SPLIT** | None recommended | Large files are well-organized |
| **DELETE** | `synonym_mapping_parse.py` | Non-functional (syntax errors) |

---

## 1. Scripts to COMBINE

### 1.1 Create plot/utils.py (HIGH PRIORITY)

**Problem:** Identical `load_data()` function in 4 files

```python
# Duplicated in 4 files (identical):
def load_data(input_file):
    """Load PAVprot output TSV file"""
    df = pd.read_csv(input_file, sep='\t')
    return df
```

| File | Line | Function |
|------|------|----------|
| `plot/plot_ipr_advanced.py` | 23 | `load_data()` |
| `plot/plot_ipr_shapes.py` | 19 | `load_data()` |
| `plot/plot_ipr_gene_level.py` | 20 | `load_data()` |
| `plot/plot_ipr_proportional_bias.py` | 20 | `load_data()` |

**Also duplicated:** Common imports and style setup in all 6 plot files:
```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
import sys
from pathlib import Path

sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
```

**Recommendation:** Create `plot/utils.py`:

```python
# plot/utils.py
"""Shared utilities for PAVprot plotting modules."""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

def setup_plot_style():
    """Configure standard plot style."""
    sns.set_style("whitegrid")
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['savefig.dpi'] = 300

def load_data(input_file):
    """Load PAVprot output TSV file."""
    df = pd.read_csv(input_file, sep='\t')
    return df

def load_pavprot_data(input_file):
    """Load and preprocess PAVprot output."""
    df = pd.read_csv(input_file, sep='\t')
    # Add any common preprocessing
    return df

def save_figure(fig, output_path, dpi=300):
    """Save figure with standard settings."""
    fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {output_path}")
```

**Then update plot files:**
```python
# In plot/plot_ipr_advanced.py (and others):
from plot.utils import load_data, setup_plot_style

setup_plot_style()
```

**Effort:** 1 hour

---

### 1.2 Combine synonym_mapping_*.py (AFTER FIXING)

**Current State:**

| File | Lines | Status |
|------|-------|--------|
| `synonym_mapping_parse.py` | 92 | **BROKEN** (syntax errors) |
| `synonym_mapping_summary.py` | 84 | Working |

**Problem:** `synonym_mapping_parse.py` has:
- IndentationError at line 59
- Two scripts concatenated together
- Syntax error `df.groupby["..."]` (brackets instead of parentheses)
- Undefined "length" column reference

**Recommendation:**

**Option A (Preferred):** Delete `synonym_mapping_parse.py` entirely
- It's non-functional
- The functionality may already exist elsewhere

**Option B:** If parsing is needed, rewrite and combine:
```
synonym_mapping_parse.py (DELETE/REWRITE)
         +                              →  synonym_mapping.py
synonym_mapping_summary.py
```

**Proposed `synonym_mapping.py`:**
```python
#!/usr/bin/env python3
"""
Synonym mapping parsing and summary generation.
Combines parsing and statistical summary functionality.
"""

class SynonymMapper:
    def __init__(self, input_file):
        self.df = pd.read_csv(input_file, sep='\t')

    def parse(self):
        """Parse synonym mapping data."""
        # Implement correct parsing logic
        pass

    def summary(self):
        """Generate summary statistics."""
        # From synonym_mapping_summary.py
        pass

    def save(self, output_prefix):
        """Save parsed data and summary."""
        pass
```

**Effort:** 2 hours (if rewriting parse functionality)

---

## 2. Scripts to SPLIT

### 2.1 pavprot.py (1,841 lines) - NO SPLIT RECOMMENDED

**Analysis:**
```
pavprot.py
├── PAVprot class (static/class methods)
│   ├── fasta2dict()          # 45 lines
│   ├── load_gff()            # 40 lines
│   ├── parse_tracking()      # 77 lines
│   ├── _assign_class_type()  # 33 lines
│   ├── compute_all_metrics() # 172 lines
│   └── ... (13 more methods)
│
├── DiamondRunner class
│   ├── diamond_blastp()      # 9 lines
│   ├── enrich_blastp()       # 58 lines
│   └── ... (4 more methods)
│
└── Standalone functions
    ├── create_argument_parser()    # 42 lines
    ├── process_interproscan_*()    # Multiple variants
    ├── write_results()             # 42 lines
    ├── aggregate_to_gene_level()   # 184 lines
    └── main()                      # 232 lines
```

**Why NOT split:**
1. All functions are closely related (single pipeline)
2. Classes provide good organization
3. Internal imports would create circular dependency risks
4. 1,841 lines is manageable for a main orchestrator

**If split were needed (NOT RECOMMENDED):**
```
pavprot.py (main)
├── pavprot_io.py        # fasta2dict, load_gff, write_results
├── pavprot_diamond.py   # DiamondRunner class
└── pavprot_interpro.py  # process_interproscan_* functions
```

---

### 2.2 run_pipeline.py (1,900 lines) - NO SPLIT RECOMMENDED

**Analysis:**
```
run_pipeline.py
├── CONFIG dict
├── Helper functions
│   ├── find_latest_output()
│   ├── check_file_exists()
│   └── mapping_type_to_colon()
│
└── PipelineRunner class
    ├── task_1_ipr_scatter()         # 66 lines
    ├── task_2_loglog_scale()        # 78 lines
    ├── task_2b_loglog_class_shapes() # 131 lines
    ├── task_3_quadrants()           # 129 lines
    ├── task_3b_quadrants_swapped()  # 129 lines
    ├── task_4_scenario_barplot()    # 85 lines
    ├── task_5_proteinx()            # 271 lines
    ├── task_6_psauron_integration() # 113 lines
    ├── task_7_psauron_plots()       # 353 lines
    └── task_8_fungidb_analysis()    # ~300 lines
```

**Why NOT split:**
1. All tasks share the same `PipelineRunner` context
2. Tasks are designed to be run selectively via CLI
3. Splitting would complicate the task discovery mechanism
4. This is in `project_scripts/` (example code, not core module)

**If split were needed (NOT RECOMMENDED):**
```
project_scripts/
├── run_pipeline.py     # Main runner + config
├── tasks_plotting.py   # task_1 through task_4
├── tasks_proteinx.py   # task_5
├── tasks_psauron.py    # task_6, task_7
└── tasks_fungidb.py    # task_8
```

---

### 2.3 gsmc.py (1,344 lines) - NO SPLIT RECOMMENDED

**Analysis:**

The file contains one main function `classify_scenarios()` with extensive logic for detecting 8 scenario types. The length comes from:
- Detailed classification logic
- Comprehensive logging
- Edge case handling

**Why NOT split:**
1. Single responsibility (scenario classification)
2. All scenario logic is interconnected
3. Splitting by scenario would create fragmented code

---

## 3. Scripts to DELETE

### 3.1 synonym_mapping_parse.py (CRITICAL)

**Status:** NON-FUNCTIONAL

**Errors:**
1. IndentationError at line 59
2. Syntax error: `df.groupby["..."]` (line 27)
3. Undefined column reference (line 28)
4. Unused import: `from curses import start_color`
5. Two scripts concatenated together

**Recommendation:** DELETE immediately

```bash
rm /Users/sadik/projects/github_prj/uolismib/gene_pav/synonym_mapping_parse.py
```

---

## 4. Summary Matrix

| Script | Action | Priority | Effort |
|--------|--------|----------|--------|
| `plot/*.py` (4 files) | **COMBINE** → `plot/utils.py` | HIGH | 1 hour |
| `synonym_mapping_parse.py` | **DELETE** | CRITICAL | 1 min |
| `synonym_mapping_summary.py` | Keep as-is (or combine after rewrite) | LOW | - |
| `pavprot.py` | Keep as-is | - | - |
| `run_pipeline.py` | Keep as-is | - | - |
| `gsmc.py` | Keep as-is | - | - |

---

## 5. Proposed File Changes

### Before:
```
gene_pav/
├── synonym_mapping_parse.py        # BROKEN - DELETE
├── synonym_mapping_summary.py      # 84 lines
├── plot/
│   ├── plot_ipr_advanced.py        # Has load_data()
│   ├── plot_ipr_shapes.py          # Has load_data()
│   ├── plot_ipr_gene_level.py      # Has load_data()
│   ├── plot_ipr_proportional_bias.py # Has load_data()
│   └── ...
```

### After:
```
gene_pav/
├── synonym_mapping_summary.py      # Keep (or rename to synonym_mapping.py)
├── plot/
│   ├── utils.py                    # NEW - shared functions
│   ├── plot_ipr_advanced.py        # Uses utils.load_data()
│   ├── plot_ipr_shapes.py          # Uses utils.load_data()
│   ├── plot_ipr_gene_level.py      # Uses utils.load_data()
│   ├── plot_ipr_proportional_bias.py # Uses utils.load_data()
│   └── ...
```

---

## 6. Implementation Order

1. **CRITICAL:** Delete `synonym_mapping_parse.py` (broken, dangerous to keep)
2. **HIGH:** Create `plot/utils.py` with shared functions
3. **HIGH:** Update 4 plot files to use `plot/utils.py`
4. **LOW:** Optionally rename `synonym_mapping_summary.py` → `synonym_mapping.py`

---

## 7. Scripts NOT to Combine/Split

The following scripts are appropriately sized and focused:

| Script | Lines | Reason to Keep As-Is |
|--------|-------|---------------------|
| `parse_interproscan.py` | 669 | Single responsibility, well-organized class |
| `bidirectional_best_hits.py` | 524 | Single responsibility |
| `pairwise_align_prot.py` | 462 | Single responsibility |
| `inconsistent_genes_transcript_IPR_PAV.py` | 451 | Single responsibility |
| `parse_liftover_extra_copy_number.py` | 435 | Single responsibility |
| `mapping_multiplicity.py` | 219 | Single responsibility |
| All `plot/*.py` files | 232-839 | Each serves distinct visualization purpose |

---

*Recommendations completed: 2026-01-19*
