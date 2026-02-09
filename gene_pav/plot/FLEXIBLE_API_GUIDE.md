# Flexible API Guide - No Hard-Coded Labels

**Principle:** All labels, titles, and identifiers are **provided as positional arguments**. Code contains **no hard-coded "ref", "Ref", "Ref/Query", "New/Old" terminology**.

## Why This Matters

**Old (Hard-Coded):**
```python
def compare_scores(data, output_dir):
    ax.scatter(data['ref_score'], data['qry_score'])
    ax.set_xlabel('Reference Score')      # ❌ Hard-coded
    ax.set_ylabel('Query Score')          # ❌ Hard-coded
    ax.set_title('Ref vs Qry Comparison') # ❌ Hard-coded
```

**Problems:**
- Can't reuse for different data sources
- Same function, different meanings in different contexts
- Difficult to adapt to new use cases

**New (Flexible - Data Agnostic):**
```python
def compare_scores(x_data, y_data, x_label, y_label, title, ax):
    ax.scatter(x_data, y_data)
    ax.set_xlabel(x_label)      # ✓ Provided by caller
    ax.set_ylabel(y_label)      # ✓ Provided by caller
    ax.set_title(title)         # ✓ Provided by caller
```

**Benefits:**
- Single function works for any comparable datasets
- Clear intent: labels indicate what data represents
- Easy to adapt and reuse

---

## Available Flexible Functions

### 1. Basic Scatter Comparison

**Module:** `gene_pav.plot.flexible_api`

```python
from gene_pav.plot.flexible_api import scatter_comparison_plot

ax = scatter_comparison_plot(
    x_data=genome_a_scores,
    y_data=genome_b_scores,
    x_label='Genome A Scores',       # Provided by caller
    y_label='Genome B Scores',       # Provided by caller
    title='Score Comparison',        # Provided by caller
    scatter_color='#1f77b4',
    add_diagonal=True,
    add_regression=True
)
```

### 2. Category-Colored Scatter

```python
from gene_pav.plot.flexible_api import colored_scatter_by_category

ax = colored_scatter_by_category(
    x_data=scores,
    y_data=confidence,
    categories=mapping_type,
    x_label='Protein Scores',        # Provided by caller
    y_label='pLDDT Confidence',      # Provided by caller
    title='Scores by Mapping Type',  # Provided by caller
    category_labels={'1to1': '1:1', '1to2N': '1:2N'},
    category_colors={'1to1': 'blue', '1to2N': 'orange'}
)
```

### 3. Distribution Comparison

```python
from gene_pav.plot.flexible_api import distribution_comparison_plot

ax = distribution_comparison_plot(
    x_data=dataset1,
    y_data=dataset2,
    x_label='Distribution X',        # Provided by caller
    y_label='Frequency',             # Provided by caller
    title='Distribution Comparison', # Provided by caller
    x_name='Dataset 1',              # Display name
    y_name='Dataset 2',              # Display name
    threshold_lines=[
        (50, 'red', 'Low threshold'),
        (70, 'orange', 'Medium threshold')
    ]
)
```

### 4. Dual Comparison (Two Metrics)

**Module:** `gene_pav.plot.flexible_psauron_plddt`

```python
from gene_pav.plot.flexible_psauron_plddt import plot_dual_comparison

plot_dual_comparison(
    x1_data=genome_a_metric1,
    y1_data=genome_b_metric1,
    x1_label='Genome A - Metric 1',     # Provided by caller
    y1_label='Genome B - Metric 1',     # Provided by caller
    x2_data=genome_a_metric2,
    y2_data=genome_b_metric2,
    x2_label='Genome A - Metric 2',     # Provided by caller
    y2_label='Genome B - Metric 2',     # Provided by caller
    title1='Metric 1 Comparison',
    title2='Metric 2 Comparison',
    output_path=Path('output/comparison.png')
)
```

### 5. Category-Colored Dual Comparison

```python
from gene_pav.plot.flexible_psauron_plddt import plot_by_category_dual

plot_by_category_dual(
    x1_data=metric1_x,
    y1_data=metric1_y,
    x1_label='Metric 1 - Dimension A',
    y1_label='Metric 1 - Dimension B',
    x2_data=metric2_x,
    y2_data=metric2_y,
    x2_label='Metric 2 - Dimension A',
    y2_label='Metric 2 - Dimension B',
    categories=classification_series,
    title1='Metric 1 by Category',
    title2='Metric 2 by Category',
    category_labels={'class1': 'Class 1', 'class2': 'Class 2'},
    category_colors={'class1': '#1f77b4', 'class2': '#ff7f0e'},
    output_path=Path('output/by_category.png')
)
```

---

## Migration Examples

### Before (Hard-Coded)

```python
# gene_pav/plot/plot_oldvsnew_psauron_plddt.py
def plot_psauron_comparison(gene_df, output_dir):
    fig, ax = plt.subplots()
    ax.scatter(gene_df['ref_psauron_score_mean'],
              gene_df['qry_psauron_score_mean'])
    ax.set_xlabel('New Annotation Psauron Score')  # ❌ Hard-coded
    ax.set_ylabel('Old Annotation Psauron Score')  # ❌ Hard-coded
    fig.savefig(output_dir / 'psauron_comparison.png')
```

### After (Flexible)

```python
# Gene-level code using flexible API
from gene_pav.plot.flexible_api import scatter_comparison_plot

scatter_comparison_plot(
    x_data=gene_df['ref_psauron_score_mean'],
    y_data=gene_df['qry_psauron_score_mean'],
    x_label='NCBI RefSeq Psauron Scores',      # ✓ Context-specific
    y_label='FungiDB Psauron Scores',          # ✓ Context-specific
    title='Psauron Score Comparison',
    output_path=output_dir / 'psauron_comparison.png'
)
```

---

## Design Pattern

All flexible functions follow this structure:

```python
def plot_something(
    # DATA INPUTS (positional, provided by caller)
    x_data: np.ndarray,
    y_data: np.ndarray,
    categories: Optional[pd.Series] = None,

    # METADATA (positional, provided by caller)
    x_label: str,           # ← Caller specifies what X represents
    y_label: str,           # ← Caller specifies what Y represents
    title: str,             # ← Caller specifies plot purpose

    # OPTIONAL STYLING (keyword, sensible defaults)
    scatter_color: str = '#1f77b4',
    scatter_alpha: float = 0.3,
    add_diagonal: bool = True,
    add_regression: bool = True,

    # OUTPUT
    ax: Optional[plt.Axes] = None,
    output_path: Optional[Path] = None,
    figure_dpi: int = 150
) -> plt.Axes or Path:
    """Function description"""
    ...
```

---

## Convention

**Never:**
- Hard-code column names in labels
- Use "ref/Ref/REF/qry/Qry/QRY" in output
- Assume data source in plot labels

**Always:**
- Accept labels as positional arguments
- Use caller-provided context
- Make functions data-agnostic

---

## Implementation Status

### ✅ Implemented
- `flexible_api.py` - Core plotting primitives
- `flexible_psauron_plddt.py` - Dual metric comparison
- This guide

### 🚧 Next Steps
1. Refactor existing plot functions to use flexible API
2. Update `__init__.py` to expose flexible functions
3. Create wrappers with sensible defaults for backward compatibility
4. Update documentation with flexible API examples
5. Gradually migrate old plotting code

---

## Questions?

If you encounter code that uses hard-coded labels:
1. Identify the plotting function
2. Extract labels as positional arguments
3. Use corresponding flexible function
4. Update callers to provide context-specific labels
