# Gene Split/Merge Detection Tool

**⚠️ CODES NOT TESTED - Validate with your datasets before production use**

A high-performance Python package for detecting gene split and merge events between two genome annotations using DIAMOND BLASTP with optional clustering analysis.

## Installation

### From Source

```bash
# Clone or download the repository
cd gene_split_merge

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Requirements

- Python 3.7+
- DIAMOND (must be installed and in PATH)
- BioPython >= 1.79
- pandas >= 1.3.0

## Quick Start

### As a Python Package

```python
from gene_split_merge import DetectGeneSplitMerge

# Initialize workflow
workflow = DetectGeneSplitMerge(
    ref_gff="data/reference.gff3",
    ref_proteins="data/reference_proteins.fasta",
    upd_gff="data/updated.gff3",
    upd_proteins="data/updated_proteins.fasta",
    output_dir="results/",
    run_clustering=True,
    clustering_workflow="linclust"
)

# Run analysis
splits, merges = workflow.run_complete_workflow()
```

### Command Line (After Installation)

```bash
# Main workflow
gene-split-merge \
    --ref-gff reference.gff3 \
    --ref-proteins reference_proteins.fasta \
    --upd-gff updated.gff3 \
    --upd-proteins updated_proteins.fasta \
    --output results/ \
    --run-clustering \
    --clustering-workflow linclust

# Standalone clustering
gene-clustering \
    --workflow linclust \
    --database all \
    --ref-proteins reference_proteins.fasta \
    --qry-proteins updated_proteins.fasta \
    --output results/clusters.tsv
```

### Using Python Module (Without Installation)

```bash
# Main workflow
python -m gene_split_merge \
    --ref-gff reference.gff3 \
    --ref-proteins reference_proteins.fasta \
    --upd-gff updated.gff3 \
    --upd-proteins updated_proteins.fasta \
    --output results/

# Or use wrapper scripts
./scripts/gene-split-merge --help
./scripts/gene-clustering --help
```

## Package Structure

```
gene_split_merge/               # Project root
├── src/                        # Source code
│   └── gene_split_merge/      # Main package
│       ├── __init__.py        # Package initialization
│       ├── __main__.py        # Module entry point
│       ├── core.py            # Main workflow
│       ├── analyzer.py        # Gene structure analysis
│       ├── clustering.py      # DIAMOND clustering
│       ├── utils.py           # DIAMOND utilities
│       └── cli_clustering.py  # Clustering CLI
├── scripts/                    # Executable scripts
│   ├── gene-split-merge       # Main CLI
│   └── gene-clustering        # Clustering CLI
├── tests/                      # Test files
├── docs/                       # Documentation
├── data/                       # Input data
├── results/                    # Output results
├── setup.py                    # Package setup
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## Features

- **Fast Protein Alignment**: DIAMOND BLASTP (10-20,000x faster than BLAST+)
- **Bidirectional Best Hits (BBH)**: Ortholog identification
- **Gene Structure Analysis**: Detect splits and merges
- **Protein Clustering**: Optional clustering with multiple algorithms
- **Modular Design**: Use as package or command-line tool

## Output Files

### Gene Split/Merge Detection

```
results/
├── gene_splits.tsv            # Split events
├── gene_merges.tsv            # Merge events
├── forward_diamond.tsv        # Forward alignments
└── reverse_diamond.tsv        # Reverse alignments
```

### Clustering (Optional)

```
results/
├── reference_proteins_diamond_linclust_clusters.tsv
├── updated_proteins_diamond_linclust_clusters.tsv
└── combined_diamond_linclust_clusters.tsv
```

## Documentation

- **[Usage Guide](docs/usage_readme.md)** - Quick usage guide with examples
- **[Design & Implementation](docs/DESIGN_AND_IMPLEMENTATION.md)** - Technical details
- **[API Documentation](docs/README.md)** - Full documentation

## Development

### Install Development Dependencies

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

### Run Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=gene_split_merge tests/
```

### Code Style

```bash
# Format code
black gene_split_merge/

# Check style
flake8 gene_split_merge/

# Type checking
mypy gene_split_merge/
```

## Citation

If you use this tool, please cite:

**DIAMOND:**
> Buchfink B, Xie C, Huson DH. (2015)
> Fast and sensitive protein alignment using DIAMOND.
> Nature Methods 12: 59-60.
> doi: 10.1038/nmeth.3176

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review test files in `tests/`
3. Verify DIAMOND installation: `diamond --version`

## Version History

- v1.5.0: Restructured as Python package with modular design
- v1.4: Multi-mode clustering with automatic ID renaming
- v1.3: Added standalone clustering CLI
- v1.2: Integrated DIAMOND clustering
- v1.1: Added bidirectional best hits (BBH)
- v1.0: Initial implementation with DIAMOND BLASTP
