# Gene Split/Merge Detection Tool - Design Methodology and Implementation

## Overview

This document describes the design principles, methodology, and implementation details of the gene split/merge detection tool.

## Design Principles

### 1. Performance-First Architecture
- **DIAMOND over BLAST**: Selected DIAMOND BLASTP for 10-20,000x speed improvement over NCBI BLAST+
- **Efficient data structures**: Union-Find algorithm for O(α(n)) clustering operations
- **Parallel processing**: Multi-threaded execution throughout the pipeline
- **Memory optimization**: Streaming I/O for large sequence files

### 2. Modular Design
- **Separation of concerns**: Each module handles a specific functionality
- **Reusability**: Components can be used standalone or integrated
- **Extensibility**: Easy to add new analysis methods or workflows

### 3. Flexibility
- **Optional features**: Clustering is opt-in, not mandatory
- **Parameter pass-through**: No hardcoded parameters - all options forwarded to DIAMOND
- **Multiple workflows**: Support for different clustering algorithms
- **Multi-mode execution**: Automatic analysis of reference, query, and combined datasets

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                  detect_gene_split_merge.py                 │
│                   (Main Workflow Orchestrator)              │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│gene_structure│ │   diamond    │ │   diamond    │
│  _analyzer   │ │  _clustering │ │   _utils     │
└──────────────┘ └──────────────┘ └──────────────┘
        │               │               │
        └───────────────┴───────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  DIAMOND Binary │
              └─────────────────┘
```

### Module Responsibilities

#### 1. detect_gene_split_merge.py
**Purpose**: Main workflow orchestration

**Key Methods**:
- `create_databases()`: Create DIAMOND databases from FASTA files
- `diamond_blastp()`: Execute reciprocal BLASTP alignment
- `parse_data()`: Parse GFF3 and alignment results
- `analyze()`: Detect split/merge events
- `export_results()`: Generate output files
- `diamond_clustering()`: Optional clustering analysis

**Design Decisions**:
- Clean method names without "step" prefixes for better API
- Optional clustering to avoid unnecessary computation
- Automatic multi-mode clustering (ref, qry, all) when enabled
- Error handling that prevents clustering failures from stopping the workflow

#### 2. gene_structure_analyzer.py
**Purpose**: Core analysis logic

**Key Features**:
- Bidirectional Best Hits (BBH) for ortholog identification
- Gene split/merge detection algorithms
- Statistical analysis of alignment quality

**Implementation Details**:
- Uses pandas DataFrames for efficient data manipulation
- Filters hits by identity, coverage, and e-value thresholds
- Merges forward and reverse hits for BBH analysis
- Calculates average identity across both directions

**Algorithm**:
```python
# BBH Algorithm
1. Filter forward hits by quality thresholds
2. Filter reverse hits by quality thresholds
3. Get best forward hit per query (lowest e-value)
4. Get best reverse hit per query (lowest e-value)
5. Merge where forward[qseqid→sseqid] matches reverse[sseqid→qseqid]
6. Calculate average identity across both directions
```

#### 3. diamond_clustering.py
**Purpose**: Protein clustering functionality

**Key Components**:

**ClusterParser**:
- Uses Union-Find data structure for efficient cluster parsing
- Path compression for O(α(n)) find operations
- Union by rank for balanced tree structure

**DiamondClusterer**:
- Supports 5 workflows: linclust, cluster, deepclust, recluster, realign
- Parameter pass-through via **kwargs
- Automatic output parsing and statistics

**Implementation Details**:
```python
class UnionFind:
    def find(self, item):
        # Path compression
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, item1, item2):
        # Union by rank
        root1, root2 = self.find(item1), self.find(item2)
        if self.rank[root1] < self.rank[root2]:
            self.parent[root1] = root2
        elif self.rank[root1] > self.rank[root2]:
            self.parent[root2] = root1
        else:
            self.parent[root2] = root1
            self.rank[root1] += 1
```

#### 4. diamond_utils.py
**Purpose**: Utility functions for DIAMOND operations

**Key Classes**:

**DiamondDatabaseManager**:
- Database creation with `makedb`
- Database information retrieval with `dbinfo`
- Validation and error handling

**DiamondOutputParser**:
- Parse tabular output (outfmt 6)
- Filter by quality metrics
- Extract best hits
- Add coverage calculations

**DiamondAlignmentAnalyzer**:
- Alignment statistics (identity, coverage distributions)
- Paralog identification
- Protein-protein interaction graph construction

**DiamondWorkflowHelper**:
- Complete workflow automation
- Bidirectional alignment execution
- Database creation + alignment in one call

#### 5. run_clustering.py
**Purpose**: Standalone clustering CLI

**Key Features**:
- Independent clustering without full workflow
- Support for ref, qry, and all database modes
- Automatic ID renaming for combined mode (_REF and _QRY suffixes)
- Space-separated parameter parsing

**ID Renaming Strategy**:
```python
# Problem: Reference and query may have identical sequence IDs
# Solution: Automatic suffix addition

Reference:  GENE_001 → GENE_001_REF
            GENE_002 → GENE_002_REF

Query:      GENE_001 → GENE_001_QRY
            GENE_002 → GENE_002_QRY

Result: No ID conflicts in combined clustering
```

## Methodology

### Gene Split Detection

**Definition**: One reference gene maps to multiple updated genes

**Scenario Diagram**:
```
Reference Genome:
─────────────────────────────────────────────────────────────────
         ┌──────────────────────────────────┐
         │         REF_GENE_001             │  (Single gene)
         └──────────────────────────────────┘
         ═══════════════════════════════════
         Position: 1000 ─────────────── 3000

                           ║
                           ║  Gene Split Event
                           ║  (e.g., annotation refinement,
                           ║   domain separation)
                           ▼

Updated Genome:
─────────────────────────────────────────────────────────────────
    ┌─────────────┐              ┌─────────────┐
    │ UPD_GENE_A  │              │ UPD_GENE_B  │  (Two genes)
    └─────────────┘              └─────────────┘
    ═══════════════              ═══════════════
    1000 ──── 1800               2000 ──── 3000

BLASTP Alignment Results:
  REF_GENE_001 ──────────────> UPD_GENE_A  (Coverage: 60%, Identity: 95%)
  REF_GENE_001 ──────────────> UPD_GENE_B  (Coverage: 40%, Identity: 92%)
```

**Algorithm**:
1. Group BLAST hits by reference gene
2. Identify hits to different updated genes
3. Filter by alignment quality thresholds
4. Validate genomic coordinates (non-overlapping in updated annotation)
5. Report split events with supporting evidence

**Criteria**:
- Minimum identity: 30%
- Minimum coverage: 50%
- Maximum e-value: 1e-5

### Gene Merge Detection

**Definition**: Multiple reference genes map to one updated gene

**Scenario Diagram**:
```
Reference Genome:
─────────────────────────────────────────────────────────────────
    ┌─────────────┐              ┌─────────────┐
    │ REF_GENE_X  │              │ REF_GENE_Y  │  (Two genes)
    └─────────────┘              └─────────────┘
    ═══════════════              ═══════════════
    1000 ──── 1800               2000 ──── 3000

                           ║
                           ║  Gene Merge Event
                           ║  (e.g., mis-annotation correction,
                           ║   fusion gene identification)
                           ▼

Updated Genome:
─────────────────────────────────────────────────────────────────
         ┌──────────────────────────────────┐
         │         UPD_GENE_001             │  (Single gene)
         └──────────────────────────────────┘
         ═══════════════════════════════════
         Position: 1000 ─────────────── 3000

BLASTP Alignment Results:
  REF_GENE_X ──────────────> UPD_GENE_001  (Coverage: 95%, Identity: 98%)
  REF_GENE_Y ──────────────> UPD_GENE_001  (Coverage: 90%, Identity: 96%)
```

**Algorithm**:
1. Group BLAST hits by updated gene
2. Identify hits from different reference genes
3. Filter by alignment quality thresholds
4. Validate genomic coordinates (non-overlapping in reference annotation)
5. Report merge events with supporting evidence

**Criteria**:
- Same as split detection
- Additional check for reciprocal best hits

### Clustering Methodology

**Workflows Available**:

#### linclust (Linear Time)
- **Use case**: Fast clustering for sequences >50% identity
- **Algorithm**: Linear time complexity, seed-and-extend
- **Parameters**: `--approx-id`, `--member-cover`
- **Performance**: Best for large datasets with high similarity

#### cluster (All-vs-All)
- **Use case**: Sensitive clustering for diverse sequences
- **Algorithm**: All-vs-all alignment with greedy incremental
- **Parameters**: `--approx-id`, `--member-cover`
- **Performance**: Slower but more sensitive

#### deepclust (Deep Clustering)
- **Use case**: Tree-of-life scale, distant homologs
- **Algorithm**: No identity cutoff, profile-based
- **Parameters**: `--member-cover`, `--cluster-steps`
- **Performance**: Detects very distant relationships

## Implementation Details

### Parameter Parsing

**Challenge**: Support flexible parameter passing to DIAMOND

**Solution**: Space-separated parameter string with automatic parsing

```python
def _parse_clustering_params(self, param_string):
    """
    Input:  "--memory-limit 64G --approx-id 90 --member-cover 80"
    Output: {'memory_limit': '64G', 'approx_id': '90', 'member_cover': '80'}
    """
    params = {}
    tokens = param_string.split()
    i = 0
    while i < len(tokens):
        if tokens[i].startswith('--'):
            key = tokens[i].lstrip('-').replace('-', '_')
            if i + 1 < len(tokens) and not tokens[i + 1].startswith('--'):
                params[key] = tokens[i + 1]
                i += 2
            else:
                params[key] = True
                i += 1
    return params
```

### File Naming Strategy

**Pattern**: `{input_basename}_diamond_{workflow}_clusters.tsv`

**Implementation**:
```python
# Extract basename from input path
base_name = Path(input_file).stem

# For reference proteins
output = f"{base_name}_diamond_linclust_clusters.tsv"
# Example: reference_proteins_diamond_linclust_clusters.tsv

# For query proteins
output = f"{base_name}_diamond_linclust_clusters.tsv"
# Example: updated_proteins_diamond_linclust_clusters.tsv

# For combined mode
output = f"combined_diamond_linclust_clusters.tsv"
```

### Multi-Mode Execution

**Rationale**: Provide comprehensive clustering analysis automatically

**Implementation**:
```python
for mode in ['ref', 'qry', 'all']:
    if mode == 'ref':
        input_file = self.ref_proteins
    elif mode == 'qry':
        input_file = self.upd_proteins
    elif mode == 'all':
        input_file = self._create_combined_proteins()

    # Run clustering workflow
    clusterer.linclust(input_file, output_file, **params)

    # Parse and report statistics
    clusters = ClusterParser.parse_file(output_file)
    stats = ClusterParser.get_statistics(clusters)
```

### Error Handling

**Philosophy**: Graceful degradation - clustering failures shouldn't stop analysis

```python
# In run_complete_workflow()
if self.run_clustering:
    try:
        self.diamond_clustering()
    except Exception as e:
        print(f"\n⚠ Warning: Clustering failed - {e}")
        # Continue with main workflow
```

## Data Flow

```
Input Files
    │
    ├─ reference.gff3 ───────────┐
    ├─ reference_proteins.fasta ─┤
    ├─ updated.gff3 ─────────────┤
    └─ updated_proteins.fasta ───┤
                                 │
                                 ▼
                        ┌────────────────┐
                        │ Create DIAMOND │
                        │   Databases    │
                        └────────┬───────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │   Reciprocal   │
                        │ DIAMOND BLASTP │
                        └────────┬───────┘
                                 │
                   ┌─────────────┼─────────────┐
                   ▼                           ▼
          forward_diamond.tsv        reverse_diamond.tsv
                   │                           │
                   └─────────────┬─────────────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │  Parse & Filter│
                        │     Results    │
                        └────────┬───────┘
                                 │
                                 ▼
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
                        └────────────────┬───────────────────────┘
                                         │
                           ┌─────────────┼─────────────┐
                           ▼                           ▼
                    gene_splits.tsv            gene_merges.tsv
                    ───────────────            ───────────────
                    ref_gene | upd_genes       ref_genes | upd_gene
                    ---------+----------       ----------+---------
                    REF_001  | GA,GB           GX,GY     | UPD_001
                    REF_002  | GC,GD,GE        GZ,GW     | UPD_002

                                         │
                                [Optional Clustering]
                                         │
                                         ▼
                           ┌─────────────────────────┐
                           │  Run clustering for:    │
                           │  - ref mode             │
                           │  - qry mode             │
                           │  - all mode (combined)  │
                           └─────────────┬───────────┘
                                         │
                           ┌─────────────┼─────────────┐
                           ▼             ▼             ▼
                   ref_..._clusters  qry_..._clusters  combined_..._clusters
```

## Performance Optimizations

### 1. DIAMOND over BLAST
- **Speedup**: 10-20,000x faster than NCBI BLAST+
- **Memory**: More memory-efficient for large datasets
- **Accuracy**: Comparable sensitivity to BLAST for most use cases

### 2. Union-Find with Path Compression
- **Time complexity**: O(α(n)) ≈ O(1) amortized per operation
- **Space complexity**: O(n) for n sequences
- **Benefit**: Efficient clustering of millions of sequences

### 3. Pandas DataFrames
- **Vectorized operations**: Faster than row-by-row processing
- **Efficient merging**: Optimized join operations for BBH
- **Memory views**: No unnecessary data copying

### 4. Streaming I/O
- **BioPython SeqIO**: Iterative parsing for large FASTA files
- **Memory footprint**: Constant regardless of file size
- **Scalability**: Can handle genome-scale datasets

## Testing Strategy

### Unit Tests
- Individual module testing in `tests/` directory
- Synthetic data generation for controlled testing
- Edge case coverage (empty inputs, single gene, etc.)

### Integration Tests
- Full workflow execution with synthetic datasets
- Clustering workflow validation
- Parameter parsing verification

### Test Files Organization
```
tests/
├── test_new_features.py         # BBH, clustering, utilities
├── test_with_synthetic_data.py  # End-to-end workflow
└── test_clustering_workflow.py  # Clustering-specific tests
```

## Code Quality Practices

### 1. Clean Method Names
- No "step" prefixes (e.g., `create_databases()` not `step1_create_databases()`)
- Descriptive names (e.g., `diamond_blastp()` clearly indicates DIAMOND BLASTP)
- Consistent naming conventions throughout

### 2. Type Hints
```python
def get_bidirectional_best_hits(
    self,
    min_identity: float = 30.0,
    min_coverage: float = 50.0
) -> pd.DataFrame:
```

### 3. Docstrings
- All public methods documented
- Parameter descriptions
- Return value specifications
- Usage examples where appropriate

### 4. Error Handling
- Informative error messages
- Graceful degradation
- User-friendly output

### 5. No Hardcoded Parameters
- All parameters passed to DIAMOND via **kwargs
- Future-proof for new DIAMOND features
- User maintains full control

## Future Enhancements

Potential improvements:
- Visualization of split/merge events
- Interactive HTML reports
- Support for additional alignment tools
- Parallelization across multiple nodes
- GPU acceleration for clustering
- Web interface for job submission

## References

### DIAMOND
- Buchfink B, Xie C, Huson DH. (2015) Fast and sensitive protein alignment using DIAMOND. Nature Methods 12: 59-60.
- DIAMOND Wiki: https://github.com/bbuchfink/diamond/wiki

### Algorithms
- Union-Find: Tarjan, R. E. (1975). "Efficiency of a Good But Not Linear Set Union Algorithm"
- BBH: Tatusov, R.L. et al. (1997). "A genomic perspective on protein families"

## Version History

- v1.0: Initial implementation with DIAMOND BLASTP
- v1.1: Added bidirectional best hits (BBH)
- v1.2: Integrated DIAMOND clustering
- v1.3: Added standalone clustering CLI
- v1.4: Multi-mode clustering with automatic ID renaming
- v1.5: Method name cleanup and documentation updates
