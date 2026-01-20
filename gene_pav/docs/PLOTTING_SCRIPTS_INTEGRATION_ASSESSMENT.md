# Assessment: Integrating project_scripts/ Plotting Scripts into plot/

> **Date:** 2026-01-19
> **Task:** Review plotting scripts and assess if any project_scripts/*.py should be integrated into main plotting scripts

---

## Executive Summary

After detailed comparison, **most features from project_scripts/ plotting files ALREADY EXIST in the main plot/ modules**.

| Feature | In project_scripts/ | In plot/ | Status |
|---------|---------------------|----------|--------|
| Regression line with R² | `plot_ipr_1to1_comparison.py` | `plot_ipr_advanced.py:84` | **ALREADY EXISTS** |
| Log-scale plots | `plot_ipr_1to1_comparison.py` | Both modules | **ALREADY EXISTS** |
| Pearson correlation | `plot_ipr_1to1_comparison.py` | `plot_ipr_comparison.py` | **ALREADY EXISTS** |
| Scenario filtering | `plot_ipr_1to1_comparison.py` | None | **MISSING - ADD** |
| Psauron analysis | `plot_psauron_*.py` | None | Cannot add (external data) |

**Action Required:** Add `--scenario` filter parameter to main plot modules.

---

## 1. Feature Comparison

### 1.1 Features in plot/plot_ipr_comparison.py (839 lines)

| Function | Lines | Feature |
|----------|-------|---------|
| `plot_scatter_by_class_type()` | 47-109 | Scatter colored by class_type |
| `plot_density_hexbin()` | 112-165 | Hexbin density plot |
| `plot_log_scale()` | 167-222 | **Log-log scale plots** ✓ |
| `plot_four_quadrants()` | 224-304 | Four quadrants analysis |
| `plot_four_quadrants_gene_level()` | 306-413 | Gene-level quadrants |
| `analyze_inconsistent_genes()` | 415-522 | Inconsistency detection |
| `plot_inconsistent_genes()` | 524-620 | Inconsistency visualization |

### 1.2 Features in plot/plot_ipr_advanced.py (232 lines)

| Function | Lines | Feature |
|----------|-------|---------|
| `plot_log_scale()` | 28-82 | **Log-log scale** ✓ |
| `plot_regression_analysis()` | 84-154 | **Regression with R², residuals, Q-Q** ✓ |
| `plot_faceted_by_emckmnj()` | 156-198 | Faceted by emckmnj flag |

### 1.3 Features in project_scripts/plot_ipr_1to1_comparison.py (295 lines)

| Feature | Line | Already in plot/? |
|---------|------|-------------------|
| Regression line with equation | 127-133 | **YES** - `plot_ipr_advanced.py:104-118` |
| Log-scale scatter | 99-120 | **YES** - Both modules |
| Pearson correlation | 74-75 | **YES** - `plot_ipr_comparison.py:83-84` |
| **Scenario filter (E only)** | 182-183 | **NO** - Missing |
| R² calculation | 75 | **YES** - `plot_ipr_advanced.py:118` |

---

## 2. Code Comparison: Regression Analysis

### project_scripts/plot_ipr_1to1_comparison.py (lines 127-133):
```python
slope, intercept, r_value, p_value, std_err = stats.linregress(
    valid[ref_col], valid[qry_col]
)
x_line = np.array([0, max_val])
y_line = slope * x_line + intercept
ax.plot(x_line, y_line, 'r-', alpha=0.7, linewidth=2,
        label=f'Regression (y={slope:.2f}x+{intercept:.0f})')
```

### plot/plot_ipr_advanced.py (lines 104-118):
```python
slope, intercept, r_value, p_value, std_err = stats.linregress(
    df_both['ref_total_ipr_domain_length'],
    df_both['query_total_ipr_domain_length'])
...
x_line = np.linspace(x.min(), x.max(), 100)
y_line = slope * x_line + intercept
ax1.plot(x_line, y_line, 'r-', linewidth=2,
         label=f'y = {slope:.2f}x + {intercept:.1f}\nR² = {r_value**2:.4f}')
```

**Conclusion:** The main module (`plot_ipr_advanced.py`) actually has a **MORE COMPLETE** regression analysis including:
- Regression line with equation ✓
- R² value ✓
- Residual plot ✓
- Q-Q plot for normality ✓

---

## 3. Only Missing Feature: Scenario Filtering

### What project_scripts/plot_ipr_1to1_comparison.py does (line 182):
```python
# Filter to scenario E (1:1)
df_e_all = df_all[df_all['scenario'] == 'E'].copy()
```

### What's needed in plot/plot_ipr_comparison.py:

**Add CLI argument:**
```python
parser.add_argument('--scenario', '-s', default=None,
                   help='Filter to specific scenario (E, A, B, J, CDI, F, G, H)')
```

**Add filtering logic:**
```python
if args.scenario:
    df = df[df['scenario'] == args.scenario].copy()
    print(f"Filtered to scenario {args.scenario}: {len(df)} entries")
```

**Effort:** 15 minutes

---

## 4. Features That CANNOT Be Added (Currently)

### 4.1 plot_psauron_distribution.py

**Requires external columns:**
- `ref_psauron_score_mean` - NOT a PAVprot output column
- `qry_psauron_score_mean` - NOT a PAVprot output column

These require running Psauron separately and merging results. Cannot be added to main plot/ modules.

### 4.2 plot_oldvsnew_psauron_plddt.py

**Requires external data files:**
- Psauron scores (external)
- ProteinX pLDDT data (external AlphaFold predictions)

Cannot be integrated - requires data not produced by PAVprot.

### 4.3 Future Integration Note

> **PLANNED:** External tool execution is planned to be consolidated into a single unified module. This will include:
> - **Psauron** - Protein structure quality scoring
> - **ProteinX/AlphaFold** - pLDDT confidence scores
> - **DIAMOND** - BLAST-based protein alignment
> - **InterProScan** - Domain/motif detection
> - **gffcompare** - GFF comparison and tracking
> - **Liftoff** - Annotation liftover
> - **Pairwise alignment** - Protein sequence alignment
>
> Once this unified external tools module is implemented, the Psauron and pLDDT visualization features can be reconsidered for integration into the main `plot/` modules.

---

## 5. Recommendations

### 5.1 ADD to plot/plot_ipr_comparison.py

| Feature | Effort | Priority |
|---------|--------|----------|
| `--scenario` filter parameter | 15 min | HIGH |

**Implementation:**
```python
# In create_argument_parser() or main():
parser.add_argument('--scenario', '-s', default=None,
                   choices=['E', 'A', 'B', 'J', 'CDI', 'F', 'G', 'H'],
                   help='Filter to specific scenario (e.g., E for 1:1 orthologs)')

# After loading data:
if args.scenario:
    original_count = len(df)
    df = df[df['scenario'] == args.scenario].copy()
    print(f"Filtered to scenario {args.scenario}: {len(df)}/{original_count} entries")
```

### 5.2 DO NOT ADD

| Feature | Reason |
|---------|--------|
| Psauron analysis | Requires external Psauron data |
| pLDDT analysis | Requires external ProteinX/AlphaFold data |

### 5.3 KEEP in project_scripts/

All three plotting scripts should remain in `project_scripts/`:
- They serve as **workflow examples** for external data integration
- They demonstrate how to combine PAVprot output with Psauron/ProteinX

---

## 6. Summary Matrix

| project_scripts/ Feature | In plot/? | Action |
|--------------------------|-----------|--------|
| Regression line | ✓ `plot_ipr_advanced.py` | None |
| R² calculation | ✓ `plot_ipr_advanced.py` | None |
| Log-scale plots | ✓ Both modules | None |
| Pearson correlation | ✓ `plot_ipr_comparison.py` | None |
| Scenario filtering | ✗ Missing | **ADD `--scenario` parameter** |
| Residual analysis | ✓ `plot_ipr_advanced.py` | None (main module is better) |
| Psauron visualization | ✗ Cannot add | Keep in project_scripts/ |
| pLDDT visualization | ✗ Cannot add | Keep in project_scripts/ |

---

## 7. Conclusion

**Surprising finding:** The main `plot/` modules are actually **MORE FEATURE-COMPLETE** than expected. The `plot_ipr_advanced.py` module already has regression analysis with:
- Regression equation
- R² value
- Residual plots
- Q-Q plots for normality testing

The only genuinely missing feature is the `--scenario` filter, which is a simple 15-minute addition.

The `project_scripts/` plotting files exist primarily because they:
1. Use **hardcoded paths** for a specific project (Fo47)
2. Integrate **external data** (Psauron, ProteinX) not produced by PAVprot
3. Filter to **specific scenarios** (which should be added as a CLI parameter)

---

## 8. Implementation Checklist

- [ ] Add `--scenario` parameter to `plot/plot_ipr_comparison.py`
- [ ] Add `--scenario` parameter to `plot/plot_ipr_advanced.py`
- [ ] Update `plot/plot_ipr_shapes.py` with scenario filter
- [ ] Update `plot/plot_ipr_gene_level.py` with scenario filter
- [ ] Document scenario filtering in README

---

*Assessment completed: 2026-01-19*
