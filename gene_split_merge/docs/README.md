# Gene Split/Merge Analyzer

**⚠️ WARNING: THIS TOOL IS UNTESTED ⚠️**

A Python toolkit for detecting gene splits and merges between two genome assemblies using DIAMOND BLASTP.

**NEW FEATURES (2025-12-06):**
- ✨ Bidirectional Best Hits (BBH) for ortholog detection
- ✨ DIAMOND clustering for redundancy removal
- ✨ Enhanced DIAMOND utilities and analysis tools

## What It Does

This tool identifies structural changes in gene models when comparing two genome assemblies of the same organism:

- **Gene Splits**: One reference gene → Multiple updated genes (1:many)
- **Gene Merges**: Multiple reference genes → One updated gene (many:1)

The analysis uses reciprocal protein alignments (DIAMOND BLASTP), genomic coordinates, and coverage analysis to detect these changes.

## Requirements

```bash
# Python packages
pip install biopython pandas numpy

# DIAMOND aligner
conda install -c bioconda diamond
```

## How to Run

### 1. Test with Synthetic Data

```bash
cd bin
python3 test_with_synthetic_data.py
```

This generates synthetic test data and validates the tool works correctly (expects 2 splits, 1 merge).

### 2. Run with Real Data

**Standard workflow:**

```bash
cd bin
python3 detect_gene_split_merge.py \
    --ref-gff ../data/reference.gff3 \
    --ref-proteins ../data/reference_proteins.fasta \
    --upd-gff ../data/updated.gff3 \
    --upd-proteins ../data/updated_proteins.fasta \
    --output ../results/ \
    --threads 28
```

**Enhanced workflow (with assembly validation):**

```bash
cd bin
python3 detect_gene_split_merge_with_assembly_validation.py \
    --ref-gff ../data/reference.gff3 \
    --ref-genome ../data/reference_genome.fasta \
    --ref-proteins ../data/reference_proteins.fasta \
    --upd-gff ../data/updated.gff3 \
    --upd-genome ../data/updated_genome.fasta \
    --upd-proteins ../data/updated_proteins.fasta \
    --output ../results/ \
    --threads 28
```

**Interactive launcher:**

```bash
cd bin
python3 launcher.py
```

## Input Files

Place your input files in the `data/` directory:

1. **reference.gff3** - Reference genome annotation (GFF3 format)
2. **reference_proteins.fasta** - Reference protein sequences (FASTA)
3. **updated.gff3** - Updated genome annotation (GFF3 format)
4. **updated_proteins.fasta** - Updated protein sequences (FASTA)

For the enhanced workflow, also include:
5. **reference_genome.fasta** - Reference genome assembly (optional)
6. **updated_genome.fasta** - Updated genome assembly (optional)

## Output Files

Results are written to the `results/` directory:

- **gene_splits.tsv** - Detected gene splits
- **gene_merges.tsv** - Detected gene merges
- **forward_diamond.tsv** - Forward alignment results
- **reverse_diamond.tsv** - Reverse alignment results
- **ref_db.dmnd** - DIAMOND database (reference)
- **upd_db.dmnd** - DIAMOND database (updated)

## Performance

DIAMOND is 10-20,000x faster than NCBI BLAST+:

| Dataset Size | Analysis Time |
|--------------|---------------|
| 10k genes    | 2-5 minutes   |
| 20k genes    | 5-15 minutes  |
| 50k genes    | 30-60 minutes |

Default: 28 CPU threads, ultra-sensitive mode

## Advanced Features

### 1. Bidirectional Best Hits (Ortholog Detection)

Find one-to-one orthologous relationships between assemblies:

```python
from gene_structure_analyzer import GeneStructureAnalyzer

# After running DIAMOND alignments...
analyzer = GeneStructureAnalyzer(ref_genes, upd_genes, forward_hits, reverse_hits)

# Get bidirectional best hits
bbh_df = analyzer.get_bidirectional_best_hits(
    min_identity=70.0,
    min_coverage=70.0
)

# Identify high-confidence orthologs
orthologs = analyzer.identify_one_to_one_orthologs(
    min_identity=80.0,
    min_coverage=70.0
)
```

### 2. DIAMOND Clustering (Redundancy Removal)

#### Command-Line Interface (Recommended)

Use the `run_clustering.py` script for easy clustering with automatic ID handling:

```bash
# Fast clustering of reference proteins
python bin/run_clustering.py \
    --workflow linclust \
    --database ref \
    --ref-proteins data/reference_proteins.fasta \
    --output results/ref_clusters.tsv \
    --params "--memory-limit 64G --approx-id 90 --member-cover 80"

# Cluster combined ref + qry (IDs automatically renamed with _REF/_QRY)
python bin/run_clustering.py \
    --workflow linclust \
    --database all \
    --ref-proteins data/reference_proteins.fasta \
    --qry-proteins data/updated_proteins.fasta \
    --output results/combined_clusters.tsv \
    --params "--memory-limit 64G --approx-id 80"
```

**Features:**
- 5 workflows: linclust, cluster, deepclust, recluster, realign
- 3 database modes: ref, qry, all (with automatic ID renaming)
- Flexible parameter specification (space-separated)

#### Python API (Advanced)

```python
from diamond_clustering import DiamondClusterer

clusterer = DiamondClusterer()

# Fast clustering at 90% identity
df = clusterer.linclust(
    input_file="proteins.fasta",
    output_file="clusters.tsv",
    approx_id=90.0,
    threads=28,
    memory_limit="64G"
)

# Get cluster statistics
stats = DiamondClusterer.get_cluster_stats(df)

# Extract representatives only
representatives = DiamondClusterer.get_cluster_representatives(df)
```

### 3. Enhanced DIAMOND Utilities

Complete DIAMOND workflows with utilities:

```python
from diamond_utils import DiamondWorkflowHelper, DiamondOutputParser

helper = DiamondWorkflowHelper()

# Create databases and run bidirectional BLASTP
forward_df, reverse_df = helper.create_and_align(
    query="ref_proteins.fasta",
    subject="upd_proteins.fasta",
    output_dir="results/",
    threads=28
)

# Filter and analyze
filtered = DiamondOutputParser.filter_by_quality(
    forward_df,
    min_identity=70.0,
    min_coverage=70.0
)
```

## Testing New Features

Run the test suite to see all new features in action:

```bash
cd bin
python3 test_new_features.py
```

## Citation

If you use DIAMOND, please cite:

> Buchfink B, Xie C, Huson DH. (2015)
> Fast and sensitive protein alignment using DIAMOND.
> Nature Methods 12: 59-60.
> doi: 10.1038/nmeth.3176

For DIAMOND clustering:

> Buchfink B, Reuter K, Drost HG. (2023)
> Sensitive clustering of protein sequences at tree-of-life scale using DIAMOND DeepClust.
> bioRxiv doi: 10.1101/2023.01.24.525373
