# Multi-Mapping Gene Relationship Scenarios

This document describes possible gene mapping patterns observed when comparing annotations between two genomes (Old/Reference vs New/Query).

> **Important:** These are observed mapping patterns, not definitive biological interpretations. Each pattern requires further investigation to determine the underlying cause.

---

## Basic Scenarios (A-D)

### Scenario A: One-to-Many Mapping

```
                    Old Gene 1
                   ┌─────────┐
Old:    ◄──────────┤         ├──────────►
                   └────┬────┘
                ┌───────┴───────┐
                ▼               ▼
           ┌─────────┐     ┌─────────┐
New:  ◄────┤  Gene 1 ├─────┤  Gene 2 ├────►
           └─────────┘     └─────────┘
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 1 | → Gene 2 |

**Pattern:** One old gene maps to two new genes

**Requires investigation:**
- Gene duplication event
- Gene split in new annotation
- Annotation artifact
- Assembly difference

**PAVprot indicators:** `old_multi_new = 1`

**Logic to investigate this scenario:**
```
1. Filter pavprot output where old_multi_new = 1
2. Group by old_gene to get all associated new_genes
3. For each group:
   - Check genomic coordinates of query genes (adjacent? same chromosome?)
   - Compare class_codes (are mappings consistent quality?)
   - Check InterProScan domains (shared domains between query genes?)
4. Output: old_gene, new_genes_list, new_genes_coordinates, domain_overlap
```

---

### Scenario B: Many-to-One Mapping

```
              Old Gene 1         Old Gene 2
             ┌─────────┐       ┌─────────┐
Old:    ◄────┤         ├───────┤         ├────►
             └────┬────┘       └────┬────┘
                  └────────┬────────┘
                           ▼
                      ┌─────────┐
New:    ◄─────────────┤  Gene 1 ├─────────────►
                      └─────────┘
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 2 | → Gene 1 |

**Pattern:** Two old genes map to one new gene

**Requires investigation:**
- Gene fusion event
- Collapsed annotation in new genome
- Assembly difference
- Tandem duplicates merged

**PAVprot indicators:** `new_multi_old = 1`

**Logic to investigate this scenario:**
```
1. Filter pavprot output where new_multi_old = 1
2. Group by new_gene to get all associated old_genes
3. For each group:
   - Check genomic coordinates of ref genes (adjacent? tandem duplicates?)
   - Compare ref gene lengths and structures
   - Check if ref genes share InterProScan domains
4. Output: new_gene, old_genes_list, old_genes_coordinates, merged_or_fused
```

---

### Scenario C: Partial Cross-Mapping (Old Gene 1 mapping two or more genes)

```
              Gene 1            Gene 2
           ┌──────────┐      ┌──────────┐
  New ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
                ↑              .    
                │           . 
                │        .
                │    .  
           ┌──────────┐      ┌──────────┐
  Old ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
              Gene 1            Gene 2

    ───────────────────────────────────────────
    Old Gene 1 ──┬──→ New Gene 1 (│ straight)
                 └──→ New Gene 2 (. diagonal)
    Old Gene 2 ─────→ New Gene 1 (. diagonal)
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 1 | → Gene 2 |
| Gene 2 | → Gene 1 |

**Pattern:** Old Gene 1 maps to both new genes; Old Gene 2 maps only to New Gene 1

**Requires investigation:**
- Complex rearrangement
- Partial homology between genes
- Domain shuffling
- Annotation boundary issues

**PAVprot indicators:** `old_multi_new = 1` AND `new_multi_old = 1` (partial)

**Logic to investigate this scenario:**
```
1. Find gene groups where BOTH old_multi_new = 1 AND new_multi_old = 1
2. Build mapping matrix for each group:
   - R1_maps_to = set of query genes R1 maps to
   - R2_maps_to = set of query genes R2 maps to
3. Classify as Scenario C when:
   - len(R1_maps_to) == 2 AND len(R2_maps_to) == 1
   - (One ref maps to both, other ref maps to one)
4. Output: cross_mapping_type = 'partial_C', involved genes, mapping matrix
```

---

### Scenario D: Full Cross-Mapping

```
              Gene 1            Gene 2
           ┌──────────┐      ┌──────────┐
  New ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
                ↑ .           .  ↑
                │     .    .     │
                │       X        │
                │     .   .      │
                │ .          .   │
           ┌──────────┐      ┌──────────┐
  Old ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
              Gene 1            Gene 2

    ───────────────────────────────────────────
    Old Gene 1 ──┬──→ New Gene 1 (│ straight)
                 └──→ New Gene 2 (. diagonal)
    Old Gene 2 ──┬──→ New Gene 1 (. diagonal)
                 └──→ New Gene 2 (│ straight)
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 1 | → Gene 2 |
| Gene 2 | → Gene 1 |
| Gene 2 | → Gene 2 |

**Pattern:** Both old genes map to both new genes

**Requires investigation:**
- Segmental duplication
- Domain shuffling
- High sequence similarity between gene pairs
- Paralogous gene families

**PAVprot indicators:** `old_multi_new = 1` AND `new_multi_old = 1` (complete)

**Logic to investigate this scenario:**
```
1. Find gene groups where BOTH old_multi_new = 1 AND new_multi_old = 1
2. Build mapping matrix for each group:
   - R1_maps_to = set of query genes R1 maps to
   - R2_maps_to = set of query genes R2 maps to
3. Classify as Scenario D when:
   - len(R1_maps_to) == 2 AND len(R2_maps_to) == 2
   - (Both refs map to both queries - full cross)
4. Check sequence similarity between all 4 genes (paralogs?)
5. Output: cross_mapping_type = 'full_D', involved genes, pairwise similarities
```

---

## Additional Scenarios (E-J)

### Scenario E: Simple 1:1 Orthology

```
              Gene 1            Gene 2
           ┌──────────┐      ┌──────────┐
  New ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
                ↑                 ↑
                │                 │
           ┌──────────┐      ┌──────────┐
  Old ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
              Gene 1            Gene 2

    ───────────────────────────────────────────
    Old Gene 1 ─────→ New Gene 1 (│ straight)
    Old Gene 2 ─────→ New Gene 2 (│ straight)
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 2 | → Gene 2 |

**Pattern:** Clean parallel mapping with no cross-relationships

**Interpretation:**
- Conserved gene structure
- True orthologous relationship
- Stable genomic region

**PAVprot indicators:** `old_multi_new = 0` AND `new_multi_old = 0`

**Logic to investigate this scenario:**
```
1. Filter pavprot output where old_multi_new = 0 AND new_multi_old = 0
2. These are true 1:1 ortholog candidates
3. For validation:
   - Check exact_match = 1 (strongest evidence)
   - Check class_code = 'em' (exact match at transcript level)
   - Verify with BBH (bidirectional best hit) if available
4. Output: ortholog pairs with confidence scores based on class_code and exact_match
```

---

### Scenario F: Swapped/Rearranged

```
              Gene 1            Gene 2
           ┌──────────┐      ┌──────────┐
  New ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
                 .               .
                    .         .
                      .    .
                        X
                    .       .
                .              .
           ┌──────────┐      ┌──────────┐
  Old ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
              Gene 1            Gene 2

    ───────────────────────────────────────────
    Old Gene 1 ─────→ New Gene 2 (. diagonal)
    Old Gene 2 ─────→ New Gene 1 (. diagonal)
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 2 |
| Gene 2 | → Gene 1 |

**Pattern:** Genes map to opposite positions

**Requires investigation:**
- Genomic rearrangement
- Chromosomal inversion
- Annotation label swap
- Translocation event

**PAVprot indicators:** Position-based analysis needed

**Logic to investigate this scenario:**
```
1. Parse GFF3 files to get genomic coordinates for all genes:
   - ref_positions = {gene_id: (chrom, start, end, strand)}
   - query_positions = {gene_id: (chrom, start, end, strand)}

2. For each 1:1 mapping pair (old_multi_new=0, new_multi_old=0):
   - Get ref gene position and query gene position
   - Find neighboring genes in both genomes

3. Detect swap pattern:
   - If old_gene_A at position P1 maps to new_gene at position Q2
   - AND old_gene_B at position P2 maps to new_gene at position Q1
   - Where P1 < P2 but Q1 > Q2 (or vice versa)
   - Flag as positional swap

4. Output: swapped gene pairs, original positions, evidence of inversion/translocation
```

---

### Scenario G: Gene Loss

```
              Gene 1            Gene 2
           ┌──────────┐      ┌──────────┐
  New ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
                ↑
                │                 ✗
                │            (no match)
           ┌──────────┐      ┌──────────┐
  Old ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
              Gene 1            Gene 2

    ───────────────────────────────────────────
    Old Gene 1 ─────→ New Gene 1 (│ straight)
    Old Gene 2 ─────→ (no match in New)
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 2 | → (none) |

**Pattern:** One old gene has no corresponding new gene

**Requires investigation:**
- True gene loss (deletion)
- Assembly gap in new genome
- Missing annotation
- Pseudogenization

**PAVprot indicators:** Gene absent from output or class code = 'u'

**Logic to investigate this scenario:**
```
1. Get complete set of reference genes from ref GFF3:
   - all_old_genes = parse_gff3(ref_gff) → set of gene IDs

2. Get set of reference genes that have mappings in pavprot output:
   - mapped_old_genes = set(pavprot_df['old_gene'].unique())

3. Calculate unmapped reference genes:
   - unmapped_ref = all_old_genes - mapped_old_genes

4. For each unmapped ref gene:
   - Get genomic coordinates from GFF3
   - Run DIAMOND blastp against query proteome to check if sequence exists
   - Check for assembly gaps at corresponding query position

5. Output: unmapped_old_genes.tsv with columns:
   - old_gene, ref_chrom, ref_start, ref_end, blast_hit_in_query, possible_cause
```

---

### Scenario H: Gene Gain

```
              Gene 1            Gene 2
           ┌──────────┐      ┌──────────┐
  New ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
                ↑                 ↑
                │                 │
                │            (no source)
           ┌──────────┐
  Old ◄────┤          ├──────────────────────►
           └──────────┘
              Gene 1

    ───────────────────────────────────────────
    Old Gene 1 ─────→ New Gene 1 (│ straight)
    (nothing)  ─────→ New Gene 2 (novel in New)
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| (none) | → Gene 2 |

**Pattern:** New gene with no old counterpart

**Requires investigation:**
- Novel gene (de novo origin)
- Horizontal gene transfer
- Annotation artifact
- Missing in old assembly/annotation

**PAVprot indicators:** Query gene not in tracking file

**Logic to investigate this scenario:**
```
1. Get complete set of query genes from query GFF3:
   - all_new_genes = parse_gff3(query_gff) → set of gene IDs

2. Get set of query genes that have mappings in pavprot output:
   - mapped_new_genes = set(pavprot_df['new_gene'].unique())

3. Calculate unmapped query genes:
   - unmapped_query = all_new_genes - mapped_new_genes

4. For each unmapped query gene:
   - Get genomic coordinates from GFF3
   - Run DIAMOND blastp against ref proteome to check if sequence exists
   - Check InterProScan for known domains (novel vs orphan gene)

5. Output: unmapped_new_genes.tsv with columns:
   - new_gene, query_chrom, query_start, query_end, blast_hit_in_ref, has_known_domains
```

---

### Scenario I: Partial Cross-Mapping (Old Gene 2 mapping two or more genes)

```
              Gene 1            Gene 2
           ┌──────────┐      ┌──────────┐
  New ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
                ↑          .     ↑
                │        .       │
                │      .         │
                │    .           │
           ┌──────────┐      ┌──────────┐
  Old ◄────┤          ├──────┤          ├────►
           └──────────┘      └──────────┘
              Gene 1            Gene 2

    ───────────────────────────────────────────
    Old Gene 1 ─────→ New Gene 1 (│ straight)
    Old Gene 2 ──┬──→ New Gene 1 (. diagonal)
                 └──→ New Gene 2 (│ straight)
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 2 | → Gene 1 |
| Gene 2 | → Gene 2 |

**Pattern:** Mirror of Scenario C - Old Gene 2 maps to both new genes; Old Gene 1 maps only to New Gene 1

**Requires investigation:**
- Similar to Scenario C but opposite gene involved
- New Gene 2 may have partial homology with both old genes
- Shared domains between old new Gene 2 and old genes
- Annotation boundary differences

**PAVprot indicators:** `old_multi_new = 1` AND `new_multi_old = 1` (partial)

**Logic to investigate this scenario:**
```
1. Find gene groups where BOTH old_multi_new = 1 AND new_multi_old = 1
2. Build mapping matrix for each group:
   - R1_maps_to = set of query genes R1 maps to
   - R2_maps_to = set of query genes R2 maps to
3. Classify as Scenario I when:
   - len(R1_maps_to) == 1 AND len(R2_maps_to) == 2
   - (One ref maps to one, other ref maps to both - mirror of C)
4. Output: cross_mapping_type = 'partial_I', involved genes, mapping matrix
```

---

### Scenario J: Higher-Order Mapping (1-to-many, 3+ genes)

```
                         Old Gene 1
                        ┌─────────┐
Old:    ◄───────────────┤         ├───────────────►
                        └────┬────┘
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐    ┌─────────┐    ┌─────────┐
New:  ◄─┤  Gene 1 ├────┤  Gene 2 ├────┤  Gene 3 ├─►
        └─────────┘    └─────────┘    └─────────┘

    Old Gene 1 ──→ New Gene 1
    Old Gene 1 ──→ New Gene 2
    Old Gene 1 ──→ New Gene 3
```

| Old | New |
|-----|-----|
| Gene 1 | → Gene 1 |
| Gene 1 | → Gene 2 |
| Gene 1 | → Gene 3 |

**Pattern:** One gene maps to 3 or more genes

**Requires investigation:**
- Extensive gene family expansion
- Tandem duplication array
- Transposable element amplification
- Assembly fragmentation

**PAVprot indicators:** `ref_query_count >= 3`

**Example from data:** `gene-FOBCDRAFT_240783` maps to 7 query genes

**Logic to investigate this scenario:**
```
1. Filter pavprot output where ref_query_count >= 3
2. Group by old_gene to get all associated new_genes
3. For each group:
   - Get genomic coordinates of all query genes
   - Check if query genes are tandemly arranged (adjacent on chromosome)
   - Calculate pairwise sequence similarity among query genes
   - Check InterProScan domains (same domains = gene family expansion)
4. Classify expansion type:
   - Tandem duplication: query genes adjacent, high similarity
   - Dispersed duplication: query genes on different chromosomes
   - Assembly fragmentation: query genes very short, incomplete
5. Output: old_gene, query_count, expansion_type, query_coordinates, similarity_matrix
```

---

## Summary Table

| Scenario | Type | Old Gene 1 maps to | Old Gene 2 maps to | Complexity |
|----------|------|--------------------|--------------------|------------|
| A | 1-to-many | New G1, New G2 | — | Low |
| B | many-to-1 | New G1 | New G1 | Low |
| C | partial cross (G1 splits) | New G1, New G2 | New G1 | Medium |
| D | full cross | New G1, New G2 | New G1, New G2 | High |
| E | 1:1 orthology | New G1 | New G2 | None |
| F | swapped | New G2 | New G1 | Medium |
| G | gene loss | New G1 | (none) | Variable |
| H | gene gain | New G1 | — (novel New G2) | Variable |
| I | partial cross (G2 splits) | New G1 | New G1, New G2 | Medium |
| J | higher-order | New G1, G2, G3+ | — | High |

---

## PAVprot Column Reference

| Column | Description |
|--------|-------------|
| `old_multi_new` | 0=exclusive 1:1, 1=one-to-many, 2=partner has others |
| `new_multi_old` | 0=exclusive 1:1, 1=many-to-one, 2=partner has others |
| `ref_query_count` | Number of query genes this ref maps to |
| `qry_ref_count` | Number of ref genes this query maps to |
| `exact_match` | 1 if all transcripts are 'em' class code |
| `class_type_gene` | Aggregated class type at gene-pair level |

---

## Implementation Status

| Scenario | Currently Detected | Data Source Needed |
|----------|-------------------|-------------------|
| A | ✓ `old_multi_new = 1` | Pavprot output |
| B | ✓ `new_multi_old = 1` | Pavprot output |
| C | ⚠️ Lumped with D, I | Pavprot output (mapping matrix) |
| D | ⚠️ Lumped with C, I | Pavprot output (mapping matrix) |
| E | ✓ Both flags = 0 | Pavprot output |
| F | ✗ Not implemented | `--gff` (genomic positions) |
| G | ✗ Not implemented | `--prot` or `--gff` (full gene list) |
| H | ✗ Not implemented | `--prot` or `--gff` (full gene list) |
| I | ⚠️ Lumped with C, D | Pavprot output (mapping matrix) |
| J | ✓ `ref_query_count >= 3` | Pavprot output |

---

## Available Data Sources in PAVprot

All scenarios can be implemented using existing pavprot inputs:

| Input | Provides | Used For |
|-------|----------|----------|
| `--gff-comp` | GffCompare tracking file | All mapping scenarios (A-E, I, J) |
| `--gff ref.gff,query.gff` | Genomic positions, full gene lists | F (positions), G/H (complete gene sets) |
| `--prot` | Reference protein sequences | G (complete ref protein list) |
| `--prot` | Query protein sequences | H (complete query protein list) |
| `--interproscan-out` | Domain annotations | Domain overlap analysis for A, B, J |

---

## Proposed New Output Files

| Scenario | Output File |
|----------|-------------|
| C, D, I | `*_cross_mapping_classified.tsv` |
| F | `*_positional_swaps.tsv` |
| G | `*_unmapped_old_genes.tsv` |
| H | `*_unmapped_new_genes.tsv` |

---

*Document generated for PAVprot analysis review*
