# Scenario Detection Implementation

This document outlines the logic for detecting gene mapping scenarios in `pavprot.py`.

---

## Final Exclusive Scenarios (Updated 2026-01-09)

All scenarios are **mutually exclusive** - a gene pair belongs to exactly one scenario.

| Scenario | `scenario` | `mapping_type` | Criteria | Status |
|----------|------------|----------------|----------|--------|
| E | `E` | `1to1` | ref→1 query AND query→1 ref (exclusive) | ✅ Active |
| A | `A` | `1to2N` | ref→exactly 2 queries, NOT in CDI | ✅ Active |
| J | `J` | `1to2N+` | ref→3+ queries, NOT in CDI | ✅ Active |
| B | `B` | `Nto1` | query→2+ refs, NOT in CDI | ✅ Active |
| CDI | `CDI` | `complex` | Cross-mapping (both sides multi) | ✅ Active |
| G | `G` | `unmapped_ref` | Ref gene with no query match | ✅ Active |
| H | `H` | `unmapped_query` | Query gene with no ref match | ✅ Active |
| F | `F` | `swap` | Positional swaps | ⏸️ **DISABLED** (TODO) |

### Exclusivity Rules

```
1. CDI takes priority over A, B, J
   - If a gene pair is in CDI, it is NOT counted in A, B, or J

2. A vs J distinction:
   - A = exactly 2 queries (1:2N)
   - J = 3 or more queries (1:2N+)

3. E is exclusive by definition:
   - Both ref and query map to exactly one partner

4. G and H are exclusive:
   - Genes NOT in pavprot output at all
```

### Mapping Type Naming Convention

| mapping_type | Meaning |
|--------------|---------|
| `1to1` | One-to-one exclusive ortholog |
| `1to2N` | One ref to exactly 2 queries |
| `1to2N+` | One ref to 3+ queries |
| `Nto1` | Multiple refs to one query |
| `complex` | Cross-mapping (CDI pattern) |
| `unmapped_ref` | Ref gene has no query match |
| `unmapped_query` | Query gene has no ref match |
| `swap` | Positional swap (DISABLED) |

---

## Implementation Status

| Scenario | Detected? | Method | Exclusive? |
|----------|-----------|--------|------------|
| E | ✅ | `ref_query_count = 1` AND `qry_ref_count = 1` | Yes |
| A | ✅ | `ref_query_count = 2` AND NOT in CDI | Yes |
| J | ✅ | `ref_query_count >= 3` AND NOT in CDI | Yes |
| B | ✅ | `qry_ref_count >= 2` AND NOT in CDI | Yes |
| CDI | ✅ | `ref_multi_query >= 1` AND `qry_multi_ref >= 1` | Yes |
| G | ✅ | ref genes NOT in pavprot output | Yes |
| H | ✅ | query genes NOT in pavprot output | Yes |
| F | ⏸️ | Positional analysis | **DISABLED** |

---

## Available Data Sources

All missing scenarios can be implemented using **existing pavprot inputs**:

| Input Argument | Data Provided | Used For Scenarios |
|----------------|---------------|-------------------|
| `--gff-comp` | GffCompare tracking file | A, B, C, D, E, I, J (mapping relationships) |
| `--gff ref.gff,query.gff` | Genomic coordinates, full gene lists | F (positions), G/H (complete gene sets) |
| `--ref-faa` | Reference protein FASTA | G (complete ref protein/gene list) |
| `--qry-faa` | Query protein FASTA | H (complete query protein/gene list) |
| `--interproscan-out` | Domain annotations | Domain analysis for all scenarios |

**Key insight:** No new input files are required. The GFF files and protein FASTAs already passed to pavprot contain all information needed.

---

## Scenario F (DISABLED - TODO)

> **Status:** ⏸️ DISABLED - Not applicable to current data. Kept as TODO for future implementation.

**Pattern:** Old Gene 1 → New Gene 2, Old Gene 2 → New Gene 1 (positional swap)

### Why Disabled
- Current analysis found 100% overlap between F and E scenarios
- Positional swap detection requires robust synteny analysis
- May produce false positives without proper validation

### Required Data (for future implementation)
- Genomic coordinates for both ref and query genes → `--gff ref.gff,query.gff`
- Chromosome/contig information → parsed from GFF3 files

### Logic (TODO)

```
1. For each gene-pair mapping, store genomic positions:
   - ref_gene_position (chromosome, start, end)
   - query_gene_position (chromosome, start, end)

2. Find pairs where:
   - ref_gene_A maps to query_gene_B
   - ref_gene_B maps to query_gene_A
   - ref_gene_A.position < ref_gene_B.position (adjacent/nearby on ref)
   - query_gene_A.position > query_gene_B.position (order reversed on query)

3. Flag as Scenario F when positional order is inverted
```

### Implementation Notes (TODO)
- Requires parsing GFF3 files to extract gene coordinates
- Need to handle cases where genes are on different chromosomes
- Consider a distance threshold for "adjacent" genes
- Should be exclusive from E (currently overlaps 100%)

---

## Scenario G

**Pattern:** Reference gene exists but has no mapping to any query gene

### Required Data
- Complete list of ALL reference genes → `--gff ref.gff` or `--ref-faa`
- Current tracking file only contains genes WITH mappings → `--gff-comp`

### Logic

```
1. Parse reference GFF3 to get set of ALL ref gene IDs

2. From pavprot output, get set of ref genes that HAVE mappings

3. Scenario G genes = ALL_ref_genes - mapped_ref_genes

4. For each unmapped ref gene:
   - Check if region exists in query assembly (optional: BLAST/alignment)
   - Check if query has annotation gap at corresponding position
```

### Implementation Notes
- Simple set difference operation
- May want to integrate with DIAMOND results to check if protein exists but wasn't annotated
- Could add column: `mapping_status = 'mapped' | 'unmapped'`

---

## Scenario H

**Pattern:** Query gene exists but has no mapping from any reference gene

### Required Data
- Complete list of ALL query genes → `--gff query.gff` or `--qry-faa`
- Current tracking file only contains genes WITH mappings → `--gff-comp`

### Logic

```
1. Parse query GFF3 to get set of ALL query gene IDs

2. From pavprot output, get set of query genes that HAVE mappings

3. Scenario H genes = ALL_query_genes - mapped_query_genes

4. For each unmapped query gene:
   - Check if region exists in reference assembly
   - Check if this is novel annotation or assembly-specific
```

### Implementation Notes
- Mirror of Scenario G logic
- Could indicate novel genes, horizontal gene transfer, or annotation artifacts
- May want to cross-reference with InterProScan to check if protein has known domains

---

## Distinguishing C, D, I

**Current Problem:** All three scenarios have `ref_multi_query=1` AND `qry_multi_ref=1`, but they represent different mapping patterns.

### Mapping Patterns

```
Scenario C:
    Old Gene 1 → New Gene 1, New Gene 2  (maps to BOTH)
    Old Gene 2 → New Gene 1              (maps to ONE)

Scenario D:
    Old Gene 1 → New Gene 1, New Gene 2  (maps to BOTH)
    Old Gene 2 → New Gene 1, New Gene 2  (maps to BOTH)

Scenario I:
    Old Gene 1 → New Gene 1              (maps to ONE)
    Old Gene 2 → New Gene 1, New Gene 2  (maps to BOTH)
```

### Logic

```
1. Identify "cross-mapping groups":
   - Find all ref genes that share at least one query gene
   - Find all query genes that share at least one ref gene
   - Build connected components of (ref_genes, query_genes)

2. For each group with 2 ref genes (R1, R2) and 2 query genes (Q1, Q2):

   Get mapping matrix:
   - R1_maps_to = {Q1?, Q2?}
   - R2_maps_to = {Q1?, Q2?}

3. Classify:

   Scenario C: R1 maps to BOTH, R2 maps to ONE
   - len(R1_maps_to) == 2 AND len(R2_maps_to) == 1

   Scenario D: BOTH map to BOTH (full cross)
   - len(R1_maps_to) == 2 AND len(R2_maps_to) == 2

   Scenario I: R1 maps to ONE, R2 maps to BOTH
   - len(R1_maps_to) == 1 AND len(R2_maps_to) == 2
```

### Proposed New Columns

| Column | Values | Description |
|--------|--------|-------------|
| `cross_mapping_type` | `none`, `partial_C`, `partial_I`, `full_D` | Type of cross-mapping pattern |
| `cross_mapping_group_id` | integer | ID to group related genes together |

### Implementation Notes
- Requires building a graph of gene relationships
- Use connected components algorithm to find groups
- Within each group, analyze the specific mapping pattern

---

## Proposed Output Columns

### For Scenario F
```
swapped_with_ref_gene    - ID of the ref gene this was swapped with
swapped_with_query_gene  - ID of the query gene this was swapped with
is_positional_swap       - 1 if detected as Scenario F
```

### For Scenarios G and H
```
mapping_status           - 'mapped' | 'ref_only' | 'query_only'
```

Or create separate output files:
- `*_unmapped_ref_genes.tsv` (Scenario G)
- `*_unmapped_query_genes.tsv` (Scenario H)

### For C, D, I Distinction
```
cross_mapping_type       - 'none' | 'partial_C' | 'partial_I' | 'full_D'
cross_mapping_group_id   - integer group identifier
```

---

## Implementation Priority

| Priority | Scenario | Complexity | Value |
|----------|----------|------------|-------|
| 1 | G, H | Low | High - identifies missing genes |
| 2 | C, D, I | Medium | Medium - refines cross-mapping |
| 3 | F | High | Low - rare cases |

---

## Code Structure Suggestion

```python
# New module: gsmc.py

def detect_unmapped_genes(pavprot_output, ref_faa, qry_faa, ref_gff=None, query_gff=None):
    """
    Detect Scenarios G and H.

    Args:
        pavprot_output: Path to pavprot TSV output
        ref_faa: Path to reference protein FASTA (--ref-faa)
        qry_faa: Path to query protein FASTA (--qry-faa)
        ref_gff: Optional path to reference GFF3 (--gff first file)
        query_gff: Optional path to query GFF3 (--gff second file)

    Returns:
        Tuple of (unmapped_ref_genes_df, unmapped_query_genes_df)
    """
    pass

def detect_positional_swaps(pavprot_output, ref_gff, query_gff):
    """
    Detect Scenario F (positional swaps).

    Args:
        pavprot_output: Path to pavprot TSV output
        ref_gff: Path to reference GFF3 (--gff first file)
        query_gff: Path to query GFF3 (--gff second file)

    Returns:
        DataFrame of swapped gene pairs with positions
    """
    pass

def classify_cross_mappings(pavprot_output):
    """
    Distinguish Scenarios C, D, I from cross-mapping groups.

    Args:
        pavprot_output: Path to pavprot TSV output

    Returns:
        DataFrame with cross_mapping_type column added
    """
    pass
```

### Integration with pavprot.py

Add new arguments to pavprot:
```
--detect-unmapped      Detect scenarios G and H (requires --ref-faa and --qry-faa)
--detect-swaps         Detect scenario F (requires --gff with 2 files)
--classify-cross       Classify cross-mappings into C, D, I
```

Or run as standalone after pavprot completes:
```bash
python gsmc.py \
    --pavprot-output pavprot_out/synonym_mapping_liftover_gffcomp.tsv \
    --ref-faa ref.faa \
    --qry-faa query.faa \
    --gff ref.gff,query.gff
```

---

*Document created for PAVprot improvement planning*
