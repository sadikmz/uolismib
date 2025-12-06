# Clustering Integration Guide

## Overview

DIAMOND clustering is integrated into the main `detect_gene_split_merge.py` workflow as an optional step that runs iteratively for reference, query, and combined protein sets.

---

## Quick Start

### Enable Clustering

Add `--run-clustering` flag to enable:

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/reference.gff3 \
    --ref-proteins data/reference_proteins.fasta \
    --upd-gff data/updated.gff3 \
    --upd-proteins data/updated_proteins.fasta \
    --output results/ \
    --run-clustering \
    --clustering-params "--memory-limit 64G --approx-id 90"
```

This automatically:
- Clusters reference proteins → `reference_proteins_diamond_linclust_clusters.tsv`
- Clusters query proteins → `updated_proteins_diamond_linclust_clusters.tsv`
- Clusters combined (ref+qry with renamed IDs) → `combined_diamond_linclust_clusters.tsv`

---

## Command-Line Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--run-clustering` | disabled | Enable clustering step |
| `--clustering-workflow` | linclust | Workflow: linclust, cluster, or deepclust |
| `--clustering-params` | None | Space-separated DIAMOND parameters |

---

## Output Files

### Naming Pattern

```
{input_basename}_diamond_{workflow}_clusters.tsv
```

### Examples

**Reference:**
```
Input:  data/reference_proteins.fasta
Output: results/reference_proteins_diamond_linclust_clusters.tsv
```

**Query:**
```
Input:  data/updated_proteins.fasta
Output: results/updated_proteins_diamond_linclust_clusters.tsv
```

**Combined:**
```
Output: results/combined_diamond_linclust_clusters.tsv
```
(IDs automatically renamed with _REF and _QRY suffixes)

---

## Workflow Modes

Clustering runs automatically for **three modes**:

### 1. Reference Mode (`ref`)
- Clusters reference proteins only
- Identifies redundancy in reference genome
- Useful for quality assessment

### 2. Query Mode (`qry`)
- Clusters query/updated proteins only
- Identifies redundancy in updated genome
- Useful for comparing assembly quality

### 3. Combined Mode (`all`)
- Combines ref + qry proteins with renamed IDs
- Reference IDs get `_REF` suffix
- Query IDs get `_QRY` suffix
- Identifies cross-assembly relationships
- Useful for comparative analysis

---

## Usage Examples

### Example 1: Fast Clustering (Default)

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/ref.gff3 \
    --ref-proteins data/ref.fasta \
    --upd-gff data/upd.gff3 \
    --upd-proteins data/upd.fasta \
    --output results/ \
    --run-clustering
```

Uses default `linclust` workflow with default parameters.

### Example 2: Custom Parameters

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/ref.gff3 \
    --ref-proteins data/ref.fasta \
    --upd-gff data/upd.gff3 \
    --upd-proteins data/upd.fasta \
    --output results/ \
    --run-clustering \
    --clustering-params "--memory-limit 64G --approx-id 90 --member-cover 80"
```

### Example 3: Sensitive Clustering

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/ref.gff3 \
    --ref-proteins data/ref.fasta \
    --upd-gff data/upd.gff3 \
    --upd-proteins data/upd.fasta \
    --output results/ \
    --run-clustering \
    --clustering-workflow cluster \
    --clustering-params "--memory-limit 64G --approx-id 50"
```

### Example 4: Deep Clustering

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/ref.gff3 \
    --ref-proteins data/ref.fasta \
    --upd-gff data/upd.gff3 \
    --upd-proteins data/upd.fasta \
    --output results/ \
    --run-clustering \
    --clustering-workflow deepclust \
    --clustering-params "--memory-limit 128G --member-cover 60"
```

---

## Console Output

```
============================================================
STEP 6: DIAMOND Clustering (Optional)
============================================================

--- Clustering mode: ref ---
  Input:  data/reference_proteins.fasta
  Output: results/reference_proteins_diamond_linclust_clusters.tsv
  ✓ Clustered 1000 sequences into 850 clusters
    Singletons: 750
    Multi-member clusters: 100

--- Clustering mode: qry ---
  Input:  data/updated_proteins.fasta
  Output: results/updated_proteins_diamond_linclust_clusters.tsv
  ✓ Clustered 1050 sequences into 880 clusters
    Singletons: 770
    Multi-member clusters: 110

--- Clustering mode: all ---
  Input:  /tmp/cluster_abc123_combined.fasta
  Output: results/combined_diamond_linclust_clusters.tsv
  ✓ Clustered 2050 sequences into 1700 clusters
    Singletons: 1520
    Multi-member clusters: 180

✓ Clustering completed for all modes
```

---

## Use Cases

### 1. Quality Assessment

Check for unexpected redundancy:

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/ref.gff3 \
    --ref-proteins data/ref.fasta \
    --upd-gff data/upd.gff3 \
    --upd-proteins data/upd.fasta \
    --output results/ \
    --run-clustering \
    --clustering-params "--approx-id 95"
```

High-identity clusters may indicate:
- Assembly errors
- Tandem duplications
- Annotation artifacts

### 2. Comparative Analysis

Compare redundancy patterns between assemblies:

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/ref.gff3 \
    --ref-proteins data/ref.fasta \
    --upd-gff data/upd.gff3 \
    --upd-proteins data/upd.fasta \
    --output results/ \
    --run-clustering \
    --clustering-workflow linclust

# Analyze cluster counts
wc -l results/*_clusters.tsv
```

### 3. Identify Conserved Gene Families

Use combined mode clustering:

```bash
python bin/detect_gene_split_merge.py \
    --ref-gff data/ref.gff3 \
    --ref-proteins data/ref.fasta \
    --upd-gff data/upd.gff3 \
    --upd-proteins data/upd.fasta \
    --output results/ \
    --run-clustering \
    --clustering-workflow cluster \
    --clustering-params "--approx-id 70"

# Look for mixed clusters (ref + qry in same cluster)
grep -E "_REF|_QRY" results/combined_diamond_cluster_clusters.tsv | \
    cut -f1 | sort | uniq -c | awk '$1 > 1'
```

---

## Error Handling

Clustering errors are **non-fatal** - the main gene split/merge workflow continues:

```
⚠ Warning: Clustering step failed: DIAMOND executable not found
  Continuing with main workflow...
```

Per-mode errors also don't stop other modes:
```
--- Clustering mode: ref ---
  ✓ Clustered successfully

--- Clustering mode: qry ---
  ✗ Error clustering qry: Out of memory

--- Clustering mode: all ---
  ✓ Clustered successfully
```

---

## Parameters Reference

All DIAMOND clustering parameters are supported via `--clustering-params`:

```bash
--clustering-params "--memory-limit 64G --approx-id 90 --member-cover 80 --mutual-cover 75 --cluster-steps faster_lin fast default"
```

See [DIAMOND Clustering Wiki](https://github.com/bbuchfink/diamond/wiki/Clustering) for full parameter list.

---

## Backward Compatibility

✅ **Fully backward compatible**

Without `--run-clustering`, the workflow runs exactly as before (no clustering).

---

## Files and Organization

**Main workflow:** `bin/detect_gene_split_merge.py`
**Test files:** `tests/` directory
**Documentation:** `docs/` directory

---

## Summary

✅ Optional clustering via `--run-clustering` flag
✅ Automatic execution for ref, qry, and combined modes
✅ Proper file naming with workflow type
✅ Automatic ID renaming for combined mode
✅ Space-separated parameter format
✅ Non-fatal error handling
✅ Fully backward compatible

For detailed DIAMOND clustering information, see `README.md` Advanced Features section.
