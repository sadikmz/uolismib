# Assessment: Integrating run_pipeline.py into pavprot.py

> **Date:** 2026-01-19
> **Task:** Assess integrating project_scripts/run_pipeline.py into the main script to allow running all or specific parts

---

## Executive Summary

**Recommendation: DO NOT INTEGRATE**

`run_pipeline.py` and `pavprot.py` serve fundamentally different purposes and should remain separate. However, a **task runner subcommand** could be added to `pavprot.py` to provide a unified entry point.

---

## 1. Comparative Analysis

### 1.1 Purpose Comparison

| Aspect | pavprot.py | run_pipeline.py |
|--------|------------|-----------------|
| **Primary Function** | Core PAVprot analysis | Downstream visualization & integration |
| **Input** | Raw files (GFF, FASTA, tracking) | PAVprot output TSV files |
| **Output** | TSV data files | PNG plots, integrated datasets |
| **Dependencies** | Core (pandas, Biopython) | Visualization (matplotlib, seaborn) |
| **Execution Order** | First | After pavprot.py completes |

### 1.2 Function Inventory

**pavprot.py (37 functions):**
```
Core Analysis:
├── fasta2dict()              # FASTA parsing
├── load_gff()                # GFF3 parsing
├── parse_tracking()          # gffcompare tracking
├── _assign_class_type()      # Classification logic
├── compute_all_metrics()     # Metric computation
├── load_extra_copy_numbers() # Liftoff parsing
├── load_interproscan_data()  # IPR domain loading
├── enrich_interproscan_data() # Data enrichment
├── detect_interproscan_type() # IPR type detection
│
DIAMOND Integration:
├── diamond_blastp()          # Forward BLAST
├── diamond_blastp_reverse()  # Reverse BLAST
├── run_bidirectional()       # BBH analysis
├── enrich_blastp()           # BLAST result integration
│
Output Generation:
├── write_results()           # TSV output
├── aggregate_to_gene_level() # Gene-level summary
└── main()                    # CLI entry point
```

**run_pipeline.py (8 task functions):**
```
Visualization Tasks:
├── task_1_ipr_scatter()       # IPR length scatter by class_type
├── task_2_loglog_scale()      # Log-log scale scatter
├── task_2b_loglog_class_shapes() # Class shapes visualization
├── task_3_quadrants()         # IPR presence quadrant analysis
├── task_3b_quadrants_swapped() # Alternative quadrant view
├── task_4_scenario_barplot()  # Scenario distribution bars
│
External Data Integration:
├── task_5_proteinx()          # ProteinX score integration
├── task_6_psauron_integration() # Psauron score integration
├── task_7_psauron_plots()     # Psauron visualization
└── task_8_fungidb_analysis()  # FungiDB species analysis
```

### 1.3 Lines of Code

| Script | Lines | Classes | Functions |
|--------|-------|---------|-----------|
| `pavprot.py` | 1,841 | 2 | 37 |
| `run_pipeline.py` | ~1,900 | 1 | 8 tasks + helpers |
| **Combined** | **~3,700** | - | - |

---

## 2. Arguments Against Integration

### 2.1 Separation of Concerns

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Flow Architecture                    │
└─────────────────────────────────────────────────────────────┘

  Raw Input Files              Core Analysis              Downstream Analysis
       │                            │                            │
       │  GFF, FASTA, tracking      │  TSV output files          │  Plots, Reports
       ▼                            ▼                            ▼
┌─────────────┐              ┌─────────────┐              ┌─────────────┐
│             │              │             │              │             │
│  pavprot.py │──────────────│   OUTPUT    │──────────────│run_pipeline │
│             │              │    TSV      │              │    .py      │
│  (ANALYSIS) │              │   FILES     │              │ (VISUALIZE) │
│             │              │             │              │             │
└─────────────┘              └─────────────┘              └─────────────┘
```

Integrating would violate the single-responsibility principle.

### 2.2 Dependency Differences

**pavprot.py dependencies:**
- pandas
- Biopython (pairwise alignment)
- subprocess (DIAMOND)
- Standard library

**run_pipeline.py dependencies:**
- pandas
- matplotlib
- seaborn
- numpy
- Project-specific external data paths

Combining would force ALL users to install visualization dependencies even if they only need core analysis.

### 2.3 External Data Requirements

`run_pipeline.py` requires project-specific external files:
```python
CONFIG = {
    "psauron_ref": Path("/Users/sadik/Documents/projects/FungiDB/..."),
    "psauron_qry": Path("/Users/sadik/Documents/projects/FungiDB/..."),
    "proteinx_ref": Path("/Users/sadik/Documents/projects/FungiDB/..."),
    "proteinx_qry": Path("/Users/sadik/Documents/projects/FungiDB/..."),
    "phytopathogen_list": Path("/Users/sadik/Documents/projects/..."),
    "fungidb_gene_stats": Path("/Users/sadik/Documents/projects/..."),
}
```

These are **not universal** - each user would need different paths.

### 2.4 Code Maintainability

| Metric | Separate | Combined |
|--------|----------|----------|
| Lines per file | ~1,900 | ~3,700 |
| Cognitive load | Lower | Higher |
| Testing | Isolated | Complex |
| Bug isolation | Easy | Harder |

---

## 3. Alternative: Unified Task Runner

Instead of integration, add a **subcommand system** to `pavprot.py`:

### 3.1 Proposed CLI Structure

```bash
# Current (keep as-is):
python pavprot.py --gff-comp tracking.file --gff ref.gff3 ...

# New subcommand:
python pavprot.py downstream --task plots --input output.tsv
python pavprot.py downstream --task psauron --config myconfig.yaml
python pavprot.py downstream --list
```

### 3.2 Implementation Sketch

```python
# In pavprot.py, add subcommand parser:

def create_argument_parser():
    parser = argparse.ArgumentParser(...)
    subparsers = parser.add_subparsers(dest='command')

    # Main analysis (default)
    analyze_parser = subparsers.add_parser('analyze', help='Run core analysis')
    # ... existing arguments ...

    # Downstream tasks
    downstream_parser = subparsers.add_parser('downstream', help='Run downstream tasks')
    downstream_parser.add_argument('--task', choices=['plots', 'psauron', 'proteinx', 'all'])
    downstream_parser.add_argument('--input', help='PAVprot output TSV')
    downstream_parser.add_argument('--config', help='YAML config for external data')
    downstream_parser.add_argument('--list', action='store_true')

    return parser

def main():
    parser = create_argument_parser()
    args = parser.parse_args()

    if args.command == 'downstream':
        from project_scripts.run_pipeline import PipelineRunner
        # ... run downstream tasks ...
    else:
        # ... existing analysis code ...
```

### 3.3 Benefits of Subcommand Approach

| Benefit | Description |
|---------|-------------|
| Single entry point | Users only need to remember `pavprot.py` |
| Lazy loading | Visualization deps only loaded when needed |
| Separation maintained | Files stay separate |
| Gradual adoption | Can be added without breaking changes |

---

## 4. If Integration Were Required

If management requires integration, here's how to do it minimally:

### 4.1 Minimal Integration Pattern

```python
# At end of pavprot.py main():

def main():
    # ... existing analysis code ...

    # Optional: run downstream tasks
    if args.run_downstream:
        from project_scripts.run_pipeline import PipelineRunner
        config = {
            "transcript_level_tsv": output_file,
            "gene_level_tsv": gene_level_file,
            "output_dir": output_dir / "downstream",
        }
        runner = PipelineRunner(config)

        if args.downstream_task == 'all':
            runner.run_all()
        else:
            getattr(runner, f'task_{args.downstream_task}')()
```

### 4.2 New Arguments Needed

```python
parser.add_argument('--run-downstream', action='store_true',
                   help='Run downstream analysis tasks after main analysis')
parser.add_argument('--downstream-task', default='all',
                   choices=['all', 'plots', 'psauron', 'proteinx'],
                   help='Which downstream task to run')
parser.add_argument('--downstream-config', type=Path,
                   help='YAML config for external data paths')
```

---

## 5. Recommendation Summary

### DO:

1. **Keep files separate** - They serve different purposes
2. **Add subcommand** - Provide unified CLI entry point
3. **Create config system** - YAML config for external data paths
4. **Document workflow** - Clear docs on when to use each

### DON'T:

1. **Don't merge code** - Would create 3,700-line monolith
2. **Don't force visualization deps** - Keep core lightweight
3. **Don't hardcode external paths** - Use configurable system

---

## 6. Workflow Recommendation

```
┌─────────────────────────────────────────────────────────────┐
│                  Recommended Workflow                        │
└─────────────────────────────────────────────────────────────┘

Step 1: Core Analysis
─────────────────────
    $ python pavprot.py \
        --gff-comp tracking.file \
        --gff ref.gff3 \
        --interproscan-out ipr.tsv \
        --output-prefix my_analysis

    Output: pavprot_out/my_analysis.tsv

Step 2: Downstream Tasks (Optional)
───────────────────────────────────
    $ python project_scripts/run_pipeline.py \
        --input pavprot_out/my_analysis.tsv \
        --task plots

    OR with proposed subcommand:

    $ python pavprot.py downstream \
        --input pavprot_out/my_analysis.tsv \
        --task plots

Step 3: Custom Analysis (Optional)
──────────────────────────────────
    # In Python:
    from project_scripts.run_pipeline import PipelineRunner
    runner = PipelineRunner(config)
    runner.task_1_ipr_scatter()
```

---

## 7. Action Items

| Priority | Action | Effort |
|----------|--------|--------|
| **P1** | Keep separate (no change) | 0 |
| **P2** | Add subcommand to pavprot.py | 2 hours |
| **P3** | Create YAML config system | 1 hour |
| **P3** | Update documentation | 1 hour |

---

## 8. Future: Unified External Tools Module

> **PLANNED DEVELOPMENT:** External tool execution is planned to be consolidated into a **single unified module**. This module will wrap and orchestrate the following external tools:
>
> | Tool | Purpose | Current Location |
> |------|---------|------------------|
> | **Psauron** | Protein structure quality scoring | External |
> | **ProteinX/AlphaFold** | pLDDT confidence scores | External |
> | **DIAMOND** | BLAST-based protein alignment | `DiamondRunner` in `pavprot.py` |
> | **InterProScan** | Domain/motif detection | `parse_interproscan.py` |
> | **gffcompare** | GFF comparison and tracking | External (output parsed) |
> | **Liftoff** | Annotation liftover | `parse_liftover_extra_copy_number.py` |
> | **Pairwise alignment** | Protein sequence alignment | `pairwise_align_prot.py` |
>
> This unified module will:
> 1. Provide a consistent interface for running external tools
> 2. Handle tool installation verification
> 3. Manage temporary files and outputs
> 4. Integrate seamlessly with both `pavprot.py` core analysis and `run_pipeline.py` downstream tasks
>
> **Impact on Integration Decision:** Once implemented, this module may change the integration calculus by providing a clean separation between:
> - **Core PAVprot analysis** (`pavprot.py`)
> - **External tool execution** (new unified module)
> - **Downstream visualization** (`run_pipeline.py` → plot modules)

---

## 9. Conclusion

**Integration is NOT recommended** because:

1. Scripts serve fundamentally different purposes
2. Different dependency requirements
3. External data paths are project-specific
4. Would create hard-to-maintain 3,700-line monolith

**Alternative:** Add a `downstream` subcommand to `pavprot.py` that imports and runs `run_pipeline.py` tasks on demand, preserving separation while providing a unified entry point.

---

*Assessment completed: 2026-01-19*
