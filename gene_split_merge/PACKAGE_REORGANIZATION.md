# Gene Split/Merge Package Reorganization - Complete

## Summary

The gene_split_merge project has been successfully reorganized into a proper Python package with modular structure. A backup of the original structure has been created.

## What Changed

### 1. Backup Created
✅ **Location**: `/Users/sadik/projects/github_prj/uolismib/uolocal/claude_code/gene_split_merge_backup`
- Complete copy of the original structure
- All files preserved for reference

### 2. New Package Structure

```
gene_split_merge/                      # Project root
├── gene_split_merge/                  # Main Python package ★
│   ├── __init__.py                   # Package initialization & exports
│   ├── __main__.py                   # Module entry point (python -m)
│   ├── core.py                       # Main workflow (was: detect_gene_split_merge.py)
│   ├── analyzer.py                   # Analysis module (was: gene_structure_analyzer.py)
│   ├── clustering.py                 # Clustering module (was: diamond_clustering.py)
│   ├── utils.py                      # Utilities (was: diamond_utils.py)
│   └── cli_clustering.py             # Clustering CLI (was: run_clustering.py)
│
├── scripts/                           # Executable wrapper scripts ★
│   ├── gene-split-merge              # Main CLI wrapper
│   └── gene-clustering               # Clustering CLI wrapper
│
├── bin/                               # Original scripts (kept for reference)
│   └── ...
│
├── tests/                             # Test files
│   ├── test_clustering_workflow.py
│   ├── test_new_features.py
│   └── test_with_synthetic_data.py
│
├── docs/                              # Documentation
│   ├── usage_readme.md
│   ├── DESIGN_AND_IMPLEMENTATION.md
│   └── README.md
│
├── setup.py                           # Package installation ★
├── requirements.txt                   # Dependencies ★
├── requirements-dev.txt               # Development dependencies ★
├── MANIFEST.in                        # Package distribution files ★
└── README.md                          # Main documentation ★
```

### 3. Module Renaming

| Original File | New Module | Purpose |
|--------------|------------|---------|
| `detect_gene_split_merge.py` | `core.py` | Main workflow orchestration |
| `gene_structure_analyzer.py` | `analyzer.py` | Gene structure analysis & BBH |
| `diamond_clustering.py` | `clustering.py` | DIAMOND clustering functionality |
| `diamond_utils.py` | `utils.py` | DIAMOND utility functions |
| `run_clustering.py` | `cli_clustering.py` | Standalone clustering CLI |

### 4. Import Updates

All modules now use **relative imports**:

```python
# Before
from gene_structure_analyzer import GFFParser
from diamond_clustering import DiamondClusterer

# After
from .analyzer import GFFParser
from .clustering import DiamondClusterer
```

### 5. New Files Created

#### Package Infrastructure
- **`gene_split_merge/__init__.py`**: Package initialization with exports
- **`gene_split_merge/__main__.py`**: Module entry point
- **`setup.py`**: Package installation configuration
- **`requirements.txt`**: Core dependencies (biopython, pandas)
- **`requirements-dev.txt`**: Development dependencies (pytest, etc.)
- **`MANIFEST.in`**: Distribution file specification

#### Documentation
- **`README.md`**: Main package documentation
- **`PACKAGE_REORGANIZATION.md`**: This file

#### Scripts
- **`scripts/gene-split-merge`**: Executable wrapper for main CLI
- **`scripts/gene-clustering`**: Executable wrapper for clustering CLI

## Usage Methods

### Method 1: Install and Use as Package

```bash
# Install the package
cd gene_split_merge
pip install -e .  # Development mode (editable)
# OR
pip install .     # Normal installation

# Use installed commands
gene-split-merge --help
gene-clustering --help

# Import in Python
python3
>>> from gene_split_merge import DetectGeneSplitMerge
>>> workflow = DetectGeneSplitMerge(...)
>>> splits, merges = workflow.run_complete_workflow()
```

### Method 2: Run as Python Module (No Installation)

```bash
cd gene_split_merge

# Run main workflow
python -m gene_split_merge \
    --ref-gff reference.gff3 \
    --ref-proteins reference_proteins.fasta \
    --upd-gff updated.gff3 \
    --upd-proteins updated_proteins.fasta \
    --output results/

# Import in scripts
import sys
sys.path.insert(0, '/path/to/gene_split_merge')
from gene_split_merge import DetectGeneSplitMerge
```

### Method 3: Use Wrapper Scripts

```bash
cd gene_split_merge

# Run main workflow
./scripts/gene-split-merge --help

# Run clustering
./scripts/gene-clustering --help
```

### Method 4: Old Method (Still Works)

```bash
# Original bin/ scripts still available for reference
python bin/detect_gene_split_merge.py --help
```

## Package API

### Main Classes Exported

```python
from gene_split_merge import (
    # Main workflow
    DetectGeneSplitMerge,

    # Core analysis
    Gene,
    BlastHit,
    GFFParser,
    BlastAnalyzer,
    GeneStructureAnalyzer,
    ResultsExporter,

    # Clustering
    ClusterParser,
    DiamondClusterer,

    # Utilities
    DiamondDatabaseManager,
    DiamondOutputParser,
    DiamondAlignmentAnalyzer,
    DiamondWorkflowHelper,
)
```

### Example Usage

```python
from gene_split_merge import DetectGeneSplitMerge

# Create workflow instance
workflow = DetectGeneSplitMerge(
    ref_gff="data/reference.gff3",
    ref_proteins="data/reference_proteins.fasta",
    upd_gff="data/updated.gff3",
    upd_proteins="data/updated_proteins.fasta",
    output_dir="results/",
    threads=32,
    run_clustering=True,
    clustering_workflow="linclust",
    clustering_params="--memory-limit 64G --approx-id 90"
)

# Run complete workflow
splits, merges = workflow.run_complete_workflow()

# Access results
print(f"Found {len(splits)} split events")
print(f"Found {len(merges)} merge events")
```

## Installation

### Install Package

```bash
cd gene_split_merge

# Install with dependencies
pip install .

# Or install in development mode (changes reflected immediately)
pip install -e .

# Install with development dependencies
pip install -e .[dev]
```

### Install Dependencies Only

```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies
pip install -r requirements-dev.txt
```

## Testing

### Test Package Import

```bash
cd gene_split_merge
python3 << 'EOF'
import gene_split_merge
print(f"Package version: {gene_split_merge.__version__}")
from gene_split_merge import DetectGeneSplitMerge
print("✓ Package imports successful!")
EOF
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=gene_split_merge tests/

# Run specific test
pytest tests/test_new_features.py -v
```

## Benefits of New Structure

### 1. **Proper Python Package**
- Can be installed with `pip install`
- Can be imported in other Python projects
- Version management through `__version__`

### 2. **Modular Design**
- Clear separation of concerns (core, analyzer, clustering, utils)
- Easy to maintain and extend
- Reusable components

### 3. **Multiple Usage Methods**
- Install as package: `pip install .`
- Run as module: `python -m gene_split_merge`
- Use wrapper scripts: `./scripts/gene-split-merge`
- Import in code: `from gene_split_merge import ...`

### 4. **Better Documentation**
- README.md at root level
- Detailed docs/ directory
- Inline documentation in `__init__.py`

### 5. **Development Tools**
- `setup.py` for package distribution
- `requirements.txt` for dependencies
- Test infrastructure with pytest
- Development dependencies separated

### 6. **Distribution Ready**
- Can be uploaded to PyPI
- Can be installed via `pip install gene-split-merge`
- MANIFEST.in for proper file inclusion

## Backward Compatibility

- ✅ Original `bin/` scripts still available (not modified)
- ✅ Old usage method still works
- ✅ All functionality preserved
- ✅ No breaking changes to existing code

## Migration Guide

### For Users

**Before:**
```bash
python bin/detect_gene_split_merge.py --ref-gff ...
```

**After (Recommended):**
```bash
# Option 1: Install and use commands
pip install .
gene-split-merge --ref-gff ...

# Option 2: Use as module
python -m gene_split_merge --ref-gff ...

# Option 3: Use wrapper scripts
./scripts/gene-split-merge --ref-gff ...
```

### For Developers

**Before:**
```python
import sys
sys.path.append('/path/to/bin')
from gene_structure_analyzer import GFFParser
```

**After:**
```python
from gene_split_merge import GFFParser
# or
from gene_split_merge.analyzer import GFFParser
```

## Directory Organization

### Active Files (Use These)
- **`gene_split_merge/`** - Main Python package
- **`scripts/`** - Executable wrapper scripts
- **`tests/`** - Test suite
- **`docs/`** - Documentation
- **`setup.py`** - Package configuration
- **`requirements.txt`** - Dependencies

### Reference/Backup Files (Keep for Reference)
- **`bin/`** - Original scripts (not modified)
- **`tmp/`** - Development notes and documentation
- **`examples/`** - Usage examples

### Backup
- **`../gene_split_merge_backup/`** - Complete backup of original structure

## Next Steps

### For Production Use

1. **Install the package:**
   ```bash
   cd gene_split_merge
   pip install .
   ```

2. **Use installed commands:**
   ```bash
   gene-split-merge --help
   gene-clustering --help
   ```

3. **Or import in your Python code:**
   ```python
   from gene_split_merge import DetectGeneSplitMerge
   ```

### For Development

1. **Install in development mode:**
   ```bash
   pip install -e .[dev]
   ```

2. **Make changes to modules in `gene_split_merge/`**

3. **Run tests:**
   ```bash
   pytest tests/
   ```

4. **Format code:**
   ```bash
   black gene_split_merge/
   ```

### For Distribution

1. **Build distribution:**
   ```bash
   python setup.py sdist bdist_wheel
   ```

2. **Upload to PyPI (when ready):**
   ```bash
   twine upload dist/*
   ```

## Verification

All package imports tested and working:
- ✅ Package import successful (v1.5.0)
- ✅ DetectGeneSplitMerge imported
- ✅ Analysis classes imported
- ✅ Clustering classes imported
- ✅ Utility classes imported
- ✅ All __all__ exports verified

## Support

For questions about the new structure:
1. Check this document (PACKAGE_REORGANIZATION.md)
2. Read README.md
3. Review docs/usage_readme.md
4. Check original backup in `../gene_split_merge_backup/`

---

**Reorganization Complete!** 🎉

The gene_split_merge project is now a proper Python package with modular structure, proper installation support, and multiple usage methods while maintaining full backward compatibility.
