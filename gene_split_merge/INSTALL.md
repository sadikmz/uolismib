# Installation Guide

## Quick Install

```bash
# 1. Navigate to the project root directory
cd /Users/sadik/projects/github_prj/uolismib/uolocal/claude_code/gene_split_merge

# 2. Install the package
pip install .
```

## Installation Directory

**IMPORTANT:** Run `pip install .` from the directory containing `setup.py`

```
gene_split_merge/              ← YOU ARE HERE (run pip install . here)
├── setup.py                   ← This file must be present
├── requirements.txt
├── src/
│   └── gene_split_merge/     ← Package source code
├── tests/
├── docs/
└── ...
```

## Installation Options

### Option 1: Normal Install
```bash
cd gene_split_merge
pip install .
```
- Installs the package to your Python environment
- Use for production/normal usage

### Option 2: Development Install (Recommended for Development)
```bash
cd gene_split_merge
pip install -e .
```
- Installs in "editable" mode
- Changes to source code are immediately reflected
- No need to reinstall after editing code
- Use when actively developing

### Option 3: Install with Development Dependencies
```bash
cd gene_split_merge
pip install -e .[dev]
```
- Installs package + development tools (pytest, etc.)
- Use for running tests and development

### Option 4: Install Dependencies Only
```bash
cd gene_split_merge
pip install -r requirements.txt
```
- Installs only biopython and pandas
- Doesn't install the gene_split_merge package itself
- Use if you only want to run scripts directly

## Verify Installation

After installation, verify it worked:

```bash
# Check if commands are available
gene-split-merge --help
gene-clustering --help

# Test Python import
python3 << 'EOF'
import gene_split_merge
print(f"✓ Successfully installed version {gene_split_merge.__version__}")
EOF
```

## Usage After Installation

Once installed, you can use it from anywhere:

```bash
# From any directory
gene-split-merge \
    --ref-gff /path/to/reference.gff3 \
    --ref-proteins /path/to/reference_proteins.fasta \
    --upd-gff /path/to/updated.gff3 \
    --upd-proteins /path/to/updated_proteins.fasta \
    --output /path/to/results/
```

Or import in your Python scripts:

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

## Without Installation

If you don't want to install, you can still use the package:

```bash
# Navigate to project root
cd /Users/sadik/projects/github_prj/uolismib/uolocal/claude_code/gene_split_merge

# Use as Python module
python -m gene_split_merge --help

# Or use wrapper scripts
./scripts/gene-split-merge --help
```

## Uninstall

```bash
pip uninstall gene-split-merge
```

## Troubleshooting

### "Could not find setup.py"
- Make sure you're in the correct directory (should contain setup.py)
- Check with: `ls setup.py`

### "Command not found: gene-split-merge"
- Make sure installation completed successfully
- Check: `pip list | grep gene-split-merge`
- Your pip bin directory might not be in PATH

### Import errors after installation
- Try reinstalling: `pip uninstall gene-split-merge && pip install .`
- Or use development mode: `pip install -e .`

### Permission errors
- Use `--user` flag: `pip install --user .`
- Or use a virtual environment (recommended)

## Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install package
pip install .

# When done, deactivate
deactivate
```

## Requirements

Before installation, ensure you have:
- Python 3.7 or higher
- pip (Python package installer)
- DIAMOND (for alignment) - must be in PATH
  - Check with: `diamond --version`
  - Install: See https://github.com/bbuchfink/diamond

## Dependencies

The package will automatically install:
- biopython >= 1.79
- pandas >= 1.3.0

Development dependencies (with `[dev]`):
- pytest >= 7.0.0
- pytest-cov >= 3.0.0
