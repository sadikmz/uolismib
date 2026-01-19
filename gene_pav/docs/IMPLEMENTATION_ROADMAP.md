# PAVprot Improvement Notes

## Current Limitations (Remaining)

### 1. Test Data Coverage
The current test data only has 1:1 gene mappings, so we can't fully verify the `ref_multi_query=1/2` and `qry_multi_ref=1/2` cases with real data.

### 2. No Proportion Information
For a gene pair with `class_code_pair="em;j"`, we don't know if it's 90% 'em' + 10% 'j' or 50/50.

### 3. Duplicate Detection Logic
`detect_one2many_mappings.py` does similar analysis separately. Could be unified with the new `ref_query_count` and `qry_ref_count` columns.

---

## Proposed Improvements (Future)

### 1. Add Proportion/Percentage for Exact Matches
```python
# exact_match_pct = 75.0  (3 out of 4 transcripts are 'em')
# This is more informative than binary exact_match=0
```
**Priority**: Medium

### 2. Gene-Level Summary Output
A separate file with one row per (ref_gene, query_gene) pair:
```
ref_gene  query_gene  transcript_count  exact_match_pct  class_code_pair  ref_query_count  qry_ref_count
GeneA     QryX        4                 25.0             em;j;m;n         2                1
GeneA     QryY        1                 100.0            em               2                1
```
**Priority**: Medium

### 3. Best Transcript Selection
Identify the "best" matching transcript for each gene pair (highest identity, or 'em' class).
**Priority**: Low

### 4. Reciprocal Best Hit Flag
```python
# reciprocal_best = 1 if this is the best match in both directions
```
**Priority**: Low (User requested to keep for future)

### 5. Unify with detect_one2many_mappings.py
The new `ref_query_count` and `qry_ref_count` columns provide similar information. Consider:
- Using pavprot output as input for detect_one2many_mappings.py
- Or integrating the detailed output generation into pavprot.py
**Priority**: Low

---

## Implementation Status

| Improvement | Status | Date | Notes |
|-------------|--------|------|-------|
| Rename class_code_multi → class_code_multi_query | ✅ Completed | 2025-12-19 | |
| Add class_code_multi_ref | ✅ Completed | 2025-12-19 | |
| Rename class_type → class_type_transcript | ✅ Completed | 2025-12-19 | |
| Add class_type_gene | ✅ Completed | 2025-12-19 | |
| Add ref_query_count column | ✅ Completed | 2025-12-19 | |
| Add qry_ref_count column | ✅ Completed | 2025-12-19 | |
| Add --filter-exact-match option | ✅ Completed | 2025-12-19 | |
| Add --filter-exclusive-1to1 option | ✅ Completed | 2025-12-19 | |
| Add --filter-class-type-gene option | ✅ Completed | 2025-12-19 | |
| Exact match percentage | Pending | | |
| Gene-level summary output | Pending | | |
| Best transcript selection | Pending | | |
| Reciprocal best hit flag | Pending | | |
| Unify with detect_one2many_mappings.py | Pending | | |

---

## Column Reference (Current Output)

### Transcript-Level Columns
| Column | Description |
|--------|-------------|
| `ref_gene` | Reference gene ID |
| `ref_transcript` | Reference transcript ID |
| `query_gene` | Query gene ID |
| `query_transcript` | Query transcript ID |
| `class_code` | GffCompare class code for this transcript pair |
| `exons` | Number of exons |

### Query-Gene Aggregated Columns
| Column | Description |
|--------|-------------|
| `class_code_multi_query` | Aggregated class codes for query_gene (across all ref genes) |
| `class_type_transcript` | Class type based on query_gene aggregation |
| `emckmnj` | 1 if any code in {em,c,k,m,n,j}, else 0 |
| `emckmnje` | 1 if any code in {em,c,k,m,n,j,e}, else 0 |

### Ref-Gene Aggregated Columns
| Column | Description |
|--------|-------------|
| `class_code_multi_ref` | Aggregated class codes for ref_gene (across all query genes) |

### Gene-Pair Level Columns
| Column | Description |
|--------|-------------|
| `class_code_pair` | Aggregated class codes for (ref_gene, query_gene) pair |
| `class_type_gene` | Class type at gene-pair level |
| `exact_match` | 1 if ALL transcripts in pair are 'em', else 0 |
| `ref_multi_transcript` | 1 if ref_gene has >1 transcripts globally |
| `qry_multi_transcript` | 1 if query_gene has >1 transcripts globally |
| `ref_multi_query` | 0=exclusive 1:1, 1=ref→multi query, 2=partner has others |
| `qry_multi_ref` | 0=exclusive 1:1, 1=query→multi ref, 2=partner has others |
| `ref_query_count` | Number of query genes this ref gene maps to |
| `qry_ref_count` | Number of ref genes this query gene maps to |

### DIAMOND Alignment Columns (with --run-diamond)
| Column | Description |
|--------|-------------|
| `pident` | Percent identity of best DIAMOND hit |
| `qcovhsp` | Query coverage (% of query aligned) |
| `scovhsp` | Subject coverage (% of reference aligned) |
| `identical_aa` | Number of identical amino acids |
| `mismatched_aa` | Number of mismatched amino acids |
| `indels_aa` | Number of indel positions |
| `aligned_aa` | Total alignment length |

### BBH Columns (with --run-bbh)
| Column | Description |
|--------|-------------|
| `is_bbh` | 1 if this is a bidirectional best hit, else 0 |
| `bbh_avg_pident` | Average pident from forward and reverse BBH |
| `bbh_avg_coverage` | Average coverage from forward and reverse BBH |

### Encoding for ref_multi_query / qry_multi_ref
- **0** = Exclusive 1:1 mapping (both sides map only to each other)
- **1** = This gene maps to multiple partners
- **2** = This gene maps to one partner, but that partner has other mappings

---

## Command-Line Filter Options

```bash
# Only output gene pairs with exact_match=1 (all transcripts are em)
--filter-exact-match

# Only output exclusive 1:1 mappings (ref_multi_query=0 AND qry_multi_ref=0)
--filter-exclusive-1to1

# Only output gene pairs with specified class_type_gene
--filter-class-type-gene "a,ackmnj"
```

---

## Class Type Reference

| class_type | Class Codes | Description |
|------------|-------------|-------------|
| `a` | em only | Exact match |
| `ckmnj` | c,k,m,n,j | Contained/partial matches |
| `e` | e only | Single exon |
| `ackmnj` | em,c,k,m,n,j | Mixed exact + partial |
| `ackmnje` | em,c,k,m,n,j,e | Mixed with single exon |
| `o` | o only | Other overlap |
| `sx` | s,x | Sense/antisense |
| `iy` | i,y | Intronic |
| `pru` | p,r,u | Other (polymerase, repeat, unknown) |

---

## Future Suggestions (2025-12-19)

### High Priority

#### 1. Add Exact Match Percentage
More informative than binary `exact_match` flag:
```python
# In gene_pair_metrics calculation (~line 340)
em_count = sum(1 for e in pair_entries if e['class_code'] == 'em')
exact_match_pct = (em_count / len(pair_entries)) * 100 if pair_entries else 0.0
```
**Status**: Pending

#### 2. Add Protein Length Difference Metric
Highlight truncations/extensions when DIAMOND results available:
```python
entry['length_diff'] = entry.get('qlen', 0) - entry.get('slen', 0)
entry['length_ratio'] = entry.get('qlen', 0) / entry.get('slen', 1) if entry.get('slen') else 0
```
**Status**: Pending

#### 3. Domain Conservation Score
Compare InterProScan domains between ref and query:
```python
def compute_domain_conservation(ref_domains: set, qry_domains: set) -> float:
    """Jaccard similarity of IPR domains between ref and query."""
    if not ref_domains and not qry_domains:
        return 1.0
    if not ref_domains or not qry_domains:
        return 0.0
    return len(ref_domains & qry_domains) / len(ref_domains | qry_domains)
```
**Status**: Pending

### Medium Priority

#### 4. Gene-Level Summary Output
Add `--gene-summary` flag for one row per gene pair:
```python
def write_gene_summary(data: dict, output_file: str):
    """Write gene-pair level summary with aggregated metrics."""
    gene_pairs = defaultdict(list)
    for entries in data.values():
        for e in entries:
            gene_pairs[(e['ref_gene'], e['query_gene'])].append(e)
    # One row per gene pair with summary stats
```
**Status**: Pending

#### 5. Add Progress Reporting
For large datasets:
```python
def report_progress(current, total, prefix="Processing"):
    if current % 10000 == 0:
        print(f"{prefix}: {current:,}/{total:,} ({100*current/total:.1f}%)", file=sys.stderr)
```
**Status**: Pending

#### 6. Add Logging Framework
Replace print statements with proper logging:
```python
import logging
logger = logging.getLogger('pavprot')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```
**Status**: Pending

#### 7. Support Compressed Input Files
Handle gzip-compressed GFF3/FASTA:
```python
def smart_open(filepath: str, mode: str = 'r'):
    """Open regular or gzip-compressed files transparently."""
    if filepath.endswith('.gz'):
        return gzip.open(filepath, mode + 't')
    return open(filepath, mode)
```
**Status**: Pending

### Lower Priority

#### 8. Add `--best-transcript` Flag
Select best transcript per gene pair:
```python
def select_best_transcript(pair_entries: list) -> dict:
    """Select best transcript: em > highest pident > longest alignment."""
    em_entries = [e for e in pair_entries if e['class_code'] == 'em']
    if em_entries:
        return max(em_entries, key=lambda x: (x.get('pident', 0), x.get('aligned_aa', 0)))
    return max(pair_entries, key=lambda x: (x.get('pident', 0), x.get('aligned_aa', 0)))
```
**Status**: Pending

#### 9. Add QC Summary Statistics
Generate summary report:
```python
def generate_qc_summary(data: dict) -> dict:
    return {
        'total_entries': sum(len(v) for v in data.values()),
        'unique_ref_genes': len(set(e['ref_gene'] for v in data.values() for e in v)),
        'unique_query_genes': len(set(e['query_gene'] for v in data.values() for e in v)),
        'exact_match_count': sum(1 for v in data.values() for e in v if e.get('exact_match')),
        'one_to_many_count': sum(1 for v in data.values() for e in v if e.get('ref_multi_query') == 1),
    }
```
**Status**: Pending

#### 10. Add JSON/Parquet Output Options
For downstream analysis:
```python
parser.add_argument('--output-format', choices=['tsv', 'json', 'parquet'], default='tsv')
```
**Status**: Pending

---

## Gene Split/Merge Integration Plan

### Overview
Future integration with `gene_split_merge` package located at:
`/Users/sadik/projects/github_prj/uolismib/gene_split_merge/`

### Current Status

#### Standalone BBH Module (Completed 2025-12-19)
Created `bidirectional_best_hits.py` - a standalone module for reciprocal best hit analysis:
- Works with pavprot's DIAMOND output format
- Designed for future integration with gene_split_merge
- Can be used standalone or imported into pavprot

**Usage:**
```bash
# Standalone
python bidirectional_best_hits.py \
    --fwd ref_vs_query_diamond.tsv.gz \
    --rev query_vs_ref_diamond.tsv.gz \
    --output bbh_results.tsv

# From pavprot
from bidirectional_best_hits import BidirectionalBestHits, enrich_pavprot_with_bbh
```

### Future Integration Tasks

#### Phase 1: BBH Integration with pavprot (Completed 2025-12-19)
- [x] Add `--run-bbh` flag to pavprot.py
- [x] Run bidirectional DIAMOND (fwd: query->ref, rev: ref->query)
- [x] Add BBH columns to main output: `is_bbh`, `bbh_avg_pident`, `bbh_avg_coverage`
- [x] Add DIAMOND coverage columns: `pident`, `qcovhsp`, `scovhsp`
- [ ] Use BBH status in filtering options (future: `--filter-bbh-only`)

#### Phase 2: gene_split_merge.GeneStructureAnalyzer Integration (Pending)
Components to integrate from gene_split_merge:
- `GeneStructureAnalyzer.detect_splits()` - 1 ref → many query
- `GeneStructureAnalyzer.detect_merges()` - many ref → 1 query
- `SyntenyAnalyzer` - flanking gene conservation scoring
- `GFFParser` - enhanced GFF parsing with transcript mapping

**Integration approach:**
```python
# Option 1: Install as package
cd /Users/sadik/projects/github_prj/uolismib/gene_split_merge
pip install -e .

# Then in pavprot:
from gene_split_merge.analyzer import GeneStructureAnalyzer
```

#### Phase 3: Unified Analysis Pipeline (Future)
Combine pavprot (GffCompare-based) and gene_split_merge (BLAST-based) for:
- Orthogonal evidence: structure + sequence similarity
- Higher confidence gene relationship calls
- Comprehensive split/merge detection with PAV context

### Key Files in gene_split_merge
| File | Key Classes/Functions |
|------|----------------------|
| `analyzer.py` | `GeneStructureAnalyzer`, `BlastAnalyzer`, `SyntenyAnalyzer` |
| `clustering.py` | Gene clustering algorithms |
| `utils.py` | Shared utilities |
| `core.py` | Core data structures |

### Notes
- gene_split_merge uses proper logging framework (something pavprot should adopt)
- gene_split_merge has dataclasses for `Gene`, `BlastHit`, `GeneRelationship`
- Both projects share similar GFF parsing needs - candidate for shared `bioutils` package
