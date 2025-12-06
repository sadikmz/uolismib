# Gene Split/Merge Detection Tool - Usage Guide

**⚠️ CODES NOT TESTED - Validate with your datasets before production use**

A high-performance tool for detecting gene split and merge events between two genome annotations using DIAMOND BLASTP.

## Quick Start

### Basic Usage (No Clustering)

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff reference.gff3 \
    --ref-proteins reference_proteins.fasta \
    --upd-gff updated.gff3 \
    --upd-proteins updated_proteins.fasta \
    --output results/
```

**Outputs:**
- `results/gene_splits.tsv` - Detected gene split events
- `results/gene_merges.tsv` - Detected gene merge events
- `results/forward_diamond.tsv` - Forward alignment results
- `results/reverse_diamond.tsv` - Reverse alignment results

### With Clustering Analysis

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff reference.gff3 \
    --ref-proteins reference_proteins.fasta \
    --upd-gff updated.gff3 \
    --upd-proteins updated_proteins.fasta \
    --output results/ \
    --run-clustering \
    --clustering-workflow linclust \
    --clustering-params "--memory-limit 64G --approx-id 90 --member-cover 80"
```

**Additional Clustering Outputs:**
- `results/reference_proteins_diamond_linclust_clusters.tsv`
- `results/updated_proteins_diamond_linclust_clusters.tsv`
- `results/combined_diamond_linclust_clusters.tsv`

## Requirements

- Python 3.7+
- DIAMOND (installed and in PATH)
- Python packages: `biopython`, `pandas`

## Installation

```bash
# Install Python packages
pip install biopython pandas

# Install DIAMOND
# See: https://github.com/bbuchfink/diamond
```

## Command-Line Options

### Required Arguments

- `--ref-gff` - Reference genome GFF3 annotation file
- `--ref-proteins` - Reference protein sequences (FASTA)
- `--upd-gff` - Updated genome GFF3 annotation file
- `--upd-proteins` - Updated protein sequences (FASTA)
- `--output` - Output directory path

### Optional Arguments

- `--threads` - Number of CPU threads (default: 28)
- `--run-clustering` - Enable protein clustering analysis
- `--clustering-workflow` - Clustering algorithm: `linclust`, `cluster`, or `deepclust` (default: linclust)
- `--clustering-params` - Space-separated DIAMOND clustering parameters

## Clustering Workflows

### linclust (Recommended for most cases)
Fast linear-time clustering for sequences with >50% identity.

```bash
--clustering-workflow linclust \
--clustering-params "--approx-id 90 --member-cover 80"
```

### cluster (Sensitive)
All-vs-all alignment, more sensitive but slower.

```bash
--clustering-workflow cluster \
--clustering-params "--approx-id 80 --member-cover 70"
```

### deepclust (Distant homologs)
For tree-of-life scale clustering, no identity cutoff required.

```bash
--clustering-workflow deepclust \
--clustering-params "--member-cover 60"
```

## Output Files

### Gene Split/Merge Results

```
┌────────────────────────────────────────┐
│       Detect Splits & Merges           │
│                                        │
│  SPLIT: 1 Ref Gene → N Upd Genes      │
│  ──────────────────────────────        │
│  Ref:  ┌─────────────┐                │
│        │ REF_GENE_001│                │
│        └─────────────┘                │
│             ║                          │
│         ════╬════                      │
│            ╱ ╲                         │
│           ▼   ▼                        │
│  Upd: ┌────┐ ┌────┐                   │
│       │ GA │ │ GB │                   │
│       └────┘ └────┘                   │
│                                        │
│  MERGE: N Ref Genes → 1 Upd Gene      │
│  ──────────────────────────────        │
│  Ref: ┌────┐ ┌────┐                   │
│       │ GX │ │ GY │                   │
│       └────┘ └────┘                   │
│           ▼   ▼                        │
│         ════╬════                      │
│             ║                          │
│  Upd:  ┌─────────────┐                │
│        │ UPD_GENE_001│                │
│        └─────────────┘                │
└────────────────────────────────────────┘
```

**gene_splits.tsv:**
Contains detected gene split events where one reference gene maps to multiple updated genes.

```
ref_gene | upd_genes
---------+----------
REF_001  | GA,GB
REF_002  | GC,GD,GE
```

**gene_merges.tsv:**
Contains detected gene merge events where multiple reference genes map to one updated gene.

```
ref_genes | upd_gene
----------+---------
GX,GY     | UPD_001
GZ,GW     | UPD_002
```

### Clustering Results

**clusters.tsv format:**
- Column 1: Centroid (representative sequence ID)
- Column 2: Member (cluster member sequence ID)

## Example Workflow

```bash
# 1. Prepare your data
ls data/
# reference.gff3
# reference_proteins.fasta
# updated.gff3
# updated_proteins.fasta

# 2. Run analysis with clustering
python bin/detect_gene_split_merge.py \
    --ref-gff data/reference.gff3 \
    --ref-proteins data/reference_proteins.fasta \
    --upd-gff data/updated.gff3 \
    --upd-proteins data/updated_proteins.fasta \
    --output results/ \
    --threads 32 \
    --run-clustering \
    --clustering-workflow linclust \
    --clustering-params "--memory-limit 128G --approx-id 90"

# 3. Check results
ls results/
```

## Standalone Clustering

You can also run clustering independently:

```bash
python bin/run_clustering.py \
    --workflow linclust \
    --database all \
    --ref-proteins reference_proteins.fasta \
    --qry-proteins updated_proteins.fasta \
    --output results/clusters.tsv \
    --params "--memory-limit 64G --approx-id 90"
```

## Performance

Typical runtimes with 28 threads:
- **10k genes**: 2-5 minutes
- **20k genes**: 5-15 minutes
- **50k genes**: 30-60 minutes

## Citation

If you use this tool, please cite:

**DIAMOND:**
> Buchfink B, Xie C, Huson DH. (2015)
> Fast and sensitive protein alignment using DIAMOND.
> Nature Methods 12: 59-60.
> doi: 10.1038/nmeth.3176

## Support

For issues or questions:
1. Check documentation in `docs/README.md`
2. Review test files in `tests/`
3. Verify DIAMOND installation: `diamond --version`
