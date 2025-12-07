# Gene Split/Merge Detection Tool

**⚠️ CODES NOT TESTED - Validate with your datasets before production use**

A simple Python implementation for detecting gene split and merge events between two genome annotations using DIAMOND BLASTP with optional clustering analysis.

## Features

- **Fast Protein Alignment**: DIAMOND BLASTP (10-20,000x faster than BLAST+)
- **Bidirectional Best Hits (BBH)**: Ortholog identification
- **Gene Structure Analysis**: Detect splits and merges
- **Protein Clustering**: Optional clustering with multiple algorithms

---

## Documentation

- **[GFF3 File Format Guide](tmp/GFF3_FORMAT.md)** - Comprehensive documentation on GFF3 format specification, structure, and usage in this tool

---

<details>
<summary><h2>🔬 Implementation</h2></summary>

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          INPUT FILES                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Reference Genome              │  Updated Genome                        │
│  • reference.gff3              │  • updated.gff3                        │
│  • reference_proteins.fasta    │  • updated_proteins.fasta              │
└──────────────┬─────────────────┴──────────────┬─────────────────────────┘
               │                                │
               ▼                                ▼
        ┌──────────────┐                ┌──────────────┐
        │   DIAMOND    │                │   DIAMOND    │
        │  makedb      │                │  makedb      │
        │  (ref_db)    │                │  (upd_db)    │
        └──────┬───────┘                └──────┬───────┘
               │                                │
               └────────────┬───────────────────┘
                            ▼
               ┌────────────────────────────┐
               │   BIDIRECTIONAL BLASTP     │
               ├────────────────────────────┤
               │  Forward:  Ref → Updated   │
               │  Reverse:  Updated → Ref   │
               └────────────┬───────────────┘
                            ▼
               ┌────────────────────────────┐
               │  PARSE BLAST ALIGNMENTS    │
               │  • Extract gene matches    │
               │  • Calculate identity/cov  │
               └────────────┬───────────────┘
                            ▼
               ┌────────────────────────────┐
               │ BIDIRECTIONAL BEST HITS    │
               │      (BBH Analysis)        │
               │  • Find reciprocal matches │
               └────────────┬───────────────┘
                            ▼
               ┌────────────────────────────┐
               │  GENE STRUCTURE ANALYSIS   │
               │  • Count gene mappings     │
               │  • Identify relationships  │
               └────────────┬───────────────┘
                            ▼
                    ┌───────┴───────┐
                    │               │
         ┌──────────▼─────┐   ┌────▼──────────┐
         │  GENE SPLITS   │   │  GENE MERGES  │
         │  (1 → Many)    │   │  (Many → 1)   │
         └──────────┬─────┘   └────┬──────────┘
                    │               │
                    └───────┬───────┘
                            ▼
               ┌────────────────────────────┐
               │      EXPORT RESULTS        │
               ├────────────────────────────┤
               │  • gene_splits.tsv         │
               │  • gene_merges.tsv         │
               │  • forward_diamond.tsv     │
               │  • reverse_diamond.tsv     │
               └────────────────────────────┘
```

**Pipeline Steps:**

1. **Database Creation** - Convert protein FASTA files to DIAMOND databases
2. **Bidirectional Alignment** - Run BLASTP in both directions (ref→upd and upd→ref)
3. **Parse Results** - Extract alignment data (identity, coverage, e-value)
4. **BBH Analysis** - Identify genes with reciprocal best matches
5. **Structure Analysis** - Detect one-to-many (splits) and many-to-one (merges) relationships
6. **Export** - Save detected events to TSV files

### Gene Split Scenario

When one gene in the reference annotation corresponds to multiple genes in the updated annotation:

```
Reference Genome:
┌─────────────────────────────────────┐
│          Gene A (full length)       │
│  ═══════════════════════════════    │
└─────────────────────────────────────┘
              ↓ BLASTP alignment
              ↓
Updated Genome:
┌──────────────┐  ┌──────────────────┐
│   Gene A1    │  │     Gene A2      │
│  ═══════════  │  │  ═══════════     │
└──────────────┘  └──────────────────┘

Detection: One reference gene → Multiple updated genes
Result: Gene SPLIT event
```

### Gene Merge Scenario

When multiple genes in the reference annotation correspond to one gene in the updated annotation:

```
Reference Genome:
┌──────────────┐  ┌──────────────────┐
│   Gene B1    │  │     Gene B2      │
│  ═══════════  │  │  ═══════════     │
└──────────────┘  └──────────────────┘
              ↓ BLASTP alignment
              ↓
Updated Genome:
┌─────────────────────────────────────┐
│          Gene B (full length)       │
│  ═══════════════════════════════    │
└─────────────────────────────────────┘

Detection: Multiple reference genes → One updated gene
Result: Gene MERGE event
```

### Analysis Method

1. **DIAMOND BLASTP**: Fast protein sequence alignment (10-20,000× faster than BLAST+)
2. **Bidirectional Best Hits (BBH)**: Identifies reciprocal best matches between annotations
3. **Gene Mapping Analysis**:
   - Counts how many genes in each annotation map to the other
   - Identifies one-to-many relationships (splits)
   - Identifies many-to-one relationships (merges)
4. **Optional Clustering**: Groups similar proteins using DIAMOND linclust/cluster/deepclust

</details>

---

<details>
<summary><h2>📦 Installation</h2></summary>

### Requirements

- Python 3.7+
- DIAMOND (must be installed and in PATH)
- BioPython >= 1.79
- pandas >= 1.3.0

### Install from Source

**IMPORTANT:** Run `pip install` from the directory containing `setup.py`

```bash
# Navigate to the package directory
cd gene_split_merge    # ← Directory containing setup.py

# Install in development mode (recommended for development)
pip install -e .

# OR install normally
pip install .
```

**Verify Installation:**
```bash
gene-split-merge --help
gene-clustering --help
```

</details>

---

<details>
<summary><h2>🚀 Quick Start</h2></summary>

### As a Python Package

```python
from gene_split_merge import DetectGeneSplitMerge

# Initialize pipeline
pipeline = DetectGeneSplitMerge(
    ref_gff="data/reference.gff3",
    ref_proteins="data/reference_proteins.fasta",
    upd_gff="data/updated.gff3",
    upd_proteins="data/updated_proteins.fasta",
    output_dir="results/",
    run_clustering=True,
    clustering_workflow="linclust"
)

# Run analysis
splits, merges = pipeline.run_complete_workflow()
```

### Command Line (After Installation)

```bash
# Main pipeline
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
# Main pipeline
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

</details>

---

<details>
<summary><h2>📁 Package Structure</h2></summary>

```
gene_split_merge/               # Project root
├── src/                        # Source code
│   └── gene_split_merge/      # Main package
│       ├── __init__.py        # Package initialization
│       ├── __main__.py        # Module entry point
│       ├── core.py            # Pipeline orchestration
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

</details>

---

<details>
<summary><h2>📊 Output Files</h2></summary>

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

</details>

---

<details>
<summary><h2>🔧 Development</h2></summary>

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=gene_split_merge tests/
```

</details>

---

<details>
<summary><h2>📖 Citation</h2></summary>

If you use this tool, please cite:

**DIAMOND:**
> Buchfink B, Xie C, Huson DH. (2015)
> Fast and sensitive protein alignment using DIAMOND.
> Nature Methods 12: 59-60.
> doi: 10.1038/nmeth.3176

</details>

---

## License

MIT License
