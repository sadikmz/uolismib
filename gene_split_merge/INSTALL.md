# Under development

## Quick Install

```bash
# 1. Navigate to the script directory 
cd src/gene_split_merge

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

### 
```bash
cd gene_split_merge
pip install .


# or Dev Install (Recommended for Development)

cd gene_split_merge
pip install -e .

# or 

cd gene_split_merge
pip install -r requirements.txt
```
- Installs only biopython and pandas

## Verify Installation

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

## Usage

```bash
gene-split-merge \
    --ref-gff /path/to/reference.gff3 \
    --ref-proteins /path/to/reference_proteins.fasta \
    --upd-gff /path/to/updated.gff3 \
    --upd-proteins /path/to/updated_proteins.fasta \
    --output /path/to/results/
```

Or it can be imported a Python scripts.

## Requirements

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
