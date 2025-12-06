# Gene Split/Merge - Clean Package Structure

## Current Package Structure (Production-Ready)

**Uses the clean `src/` layout to avoid naming conflicts!**

```
gene_split_merge/                  # Project root directory
├── src/                          # Source code directory
│   └── gene_split_merge/        # Main Python package ★
│       ├── __init__.py          # Package initialization & exports
│       ├── __main__.py          # Module entry point (python -m)
│       ├── core.py              # Main workflow orchestration
│       ├── analyzer.py          # Gene structure analysis & BBH
│       ├── clustering.py        # DIAMOND clustering functionality
│       ├── utils.py             # DIAMOND utility functions
│       └── cli_clustering.py    # Standalone clustering CLI
│
├── scripts/                      # Executable wrapper scripts
│   ├── gene-split-merge         # Main workflow CLI
│   └── gene-clustering          # Clustering CLI
│
├── tests/                        # Test suite
│   ├── test_clustering_workflow.py
│   ├── test_new_features.py
│   └── test_with_synthetic_data.py
│
├── docs/                         # Documentation
│   ├── usage_readme.md          # Quick usage guide
│   ├── DESIGN_AND_IMPLEMENTATION.md  # Technical details
│   ├── README.md                # Full documentation
│   └── CLUSTERING_INTEGRATION.md # Clustering guide
│
├── data/                         # Input data directory
│   └── README.md
│
├── results/                      # Output results directory
│
├── setup.py                      # Package installation ★
├── requirements.txt              # Core dependencies
├── requirements-dev.txt          # Development dependencies
├── MANIFEST.in                   # Distribution configuration
├── README.md                     # Main documentation
├── PACKAGE_REORGANIZATION.md     # Reorganization guide
├── PACKAGE_STRUCTURE.md          # This file
└── .gitignore                    # Git ignore rules
```

**Note:** The `src/` layout eliminates the naming conflict between the project directory `gene_split_merge/` and the package directory. This is a recommended Python packaging pattern.

## File Count

**Production Files:**
- Python modules: 7
- Scripts: 2
- Tests: 3
- Docs: 4
- Config: 5
- **Total: 21 active files**

**Backup Files:**
- Moved to `gene_split_merge_backup/`
- Original scripts, temporary files, old examples

## Usage

### Install Package

```bash
cd gene_split_merge
pip install .
```

### Use Commands

```bash
# Main workflow
gene-split-merge --help

# Clustering
gene-clustering --help
```

### Import in Python

```python
from gene_split_merge import DetectGeneSplitMerge

workflow = DetectGeneSplitMerge(
    ref_gff="reference.gff3",
    ref_proteins="reference_proteins.fasta",
    upd_gff="updated.gff3",
    upd_proteins="updated_proteins.fasta",
    output_dir="results/"
)

splits, merges = workflow.run_complete_workflow()
```

### Run as Module

```bash
python -m gene_split_merge --help
```

### Use Wrapper Scripts

```bash
./scripts/gene-split-merge --help
./scripts/gene-clustering --help
```

## Key Features

✅ **Proper Python Package** - Install with pip
✅ **Modular Design** - Clean separation of concerns
✅ **Multiple Usage Methods** - Package, module, or scripts
✅ **Full Documentation** - Comprehensive docs/
✅ **Test Suite** - pytest-ready tests
✅ **Distribution Ready** - Can publish to PyPI
✅ **Backward Compatible** - Original files in backup

## Development

### Install in Dev Mode

```bash
pip install -e .[dev]
```

### Run Tests

```bash
pytest tests/
pytest --cov=gene_split_merge tests/
```

### Code Style

```bash
black gene_split_merge/
flake8 gene_split_merge/
mypy gene_split_merge/
```

## Package API

```python
from gene_split_merge import (
    # Main workflow
    DetectGeneSplitMerge,

    # Analysis
    Gene, BlastHit, GFFParser,
    BlastAnalyzer, GeneStructureAnalyzer,
    ResultsExporter,

    # Clustering
    ClusterParser, DiamondClusterer,

    # Utilities
    DiamondDatabaseManager,
    DiamondOutputParser,
    DiamondAlignmentAnalyzer,
    DiamondWorkflowHelper,
)
```

## Clean & Production Ready! 🎉

The package structure is now clean, modular, and ready for:
- ✅ Production use
- ✅ Distribution (PyPI)
- ✅ Integration into other projects
- ✅ Continued development
