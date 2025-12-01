# InterProScan Parser

A comprehensive Python tool for running InterProScan and parsing its output files in various formats (TSV, XML, JSON, GFF3).

## Features

- Run InterProScan directly from the script
- Parse existing InterProScan output files
- Support for multiple formats: TSV, XML, JSON, GFF3
- Select longest domain when proteins match multiple domains
- Generate domain length distribution statistics
- Export parsed results to JSON or TSV
- Export domain statistics to JSON or TSV

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)
- InterProScan (only if using `--run` mode)

## Usage

### Mode 1: Parse Existing Output

Parse an existing InterProScan TSV output (with auto-generated output filename):

```bash
python parse_interproscan.py --parse results.tsv
# Creates: results_parsed.tsv (default is TSV format)
```

Parse with explicit output filename:

```bash
# JSON output
python parse_interproscan.py --parse results.tsv --output-parsed parsed_results.json

# TSV output
python parse_interproscan.py --parse results.tsv --output-parsed-tsv parsed_results.tsv
```

Parse InterProScan TSV (always 15 columns):

```bash
python parse_interproscan.py --parse results.tsv
# Creates: results_parsed.tsv (14 columns - pathways excluded)
# GO terms (column 14) are automatically included if present
# Pathway annotations (column 15) are stored internally, excluded from TSV output
```

Parse GFF3 format (auto-detected):

```bash
python parse_interproscan.py --parse results.gff3
# Auto-detects GFF3 format from extension
# Creates: results_parsed.tsv
```

Parse XML format (auto-detected):

```bash
python parse_interproscan.py --parse results.xml
# Auto-detects XML format from extension
# Creates: results_parsed.tsv
```

Parse JSON format (auto-detected):

```bash
python parse_interproscan.py --parse results.json
# Auto-detects JSON format from extension
# Creates: results_parsed.tsv
```

### Mode 2: Run InterProScan and Parse

Run InterProScan and parse the output (uses input file basename by default):

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --format TSV \
    --cpu 8
# Creates: proteins.tsv (InterProScan output)
# InterProScan runs with --iprlookup and --goterms enabled by default
```

Run with custom output basename:

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --output-base myanalysis \
    --format TSV \
    --cpu 8
# Creates: myanalysis.tsv (InterProScan output)
```

Run with pathways (--iprlookup and --goterms are always included):

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --output-base results \
    --format TSV \
    --cpu 8 \
    --pathways
# InterProScan runs with --iprlookup, --goterms, and --pathways
```

Run with specific databases:

```bash
python parse_interproscan.py \
    --run \
    --input proteins.fasta \
    --output-base results \
    --databases Pfam,PRINTS,Gene3D \
    --cpu 4
```

### Longest Domain Analysis

Select only the longest domain for each protein and generate statistics.

**Auto-generated filenames** (simplest approach):

```bash
python parse_interproscan.py --parse results.tsv --longest-domain
# Creates 8 files:
# Overall longest domains (any database):
#   - results_longest_domains.json
#   - results_longest_domains.tsv
#   - results_domain_distribution.json
#   - results_domain_distribution.tsv
# Longest InterPro-annotated domains (IPR prefix only):
#   - results_longest_domains_NotintAnn.json
#   - results_longest_domains_NotintAnn.tsv
#   - results_domain_distribution_NotintAnn.json
#   - results_domain_distribution_NotintAnn.tsv
```

**Note**: The `_NotintAnn` suffix indicates files containing only InterPro-annotated domains (entries with `interpro_accession` starting with "IPR"). This is useful when the overall longest domain comes from a database other than InterPro, allowing you to see the longest InterPro-specific annotation separately.

**Explicit filenames** for JSON only:

```bash
python parse_interproscan.py \
    --parse results.tsv \
    --longest-domain \
    --domain-stats domain_distribution.json \
    --output-parsed longest_domains.json
```

**Explicit filenames** for TSV only:

```bash
python parse_interproscan.py \
    --parse results.tsv \
    --longest-domain \
    --domain-stats-tsv domain_distribution.tsv \
    --output-parsed-tsv longest_domains.tsv
```

**Export to both JSON and TSV** with custom names:

```bash
python parse_interproscan.py \
    --parse results.tsv \
    --longest-domain \
    --domain-stats domain_distribution.json \
    --domain-stats-tsv domain_distribution.tsv \
    --output-parsed longest_domains.json \
    --output-parsed-tsv longest_domains.tsv
```

## Command-Line Arguments

### General Options

- `--run`: Run InterProScan before parsing
- `--parse FILE`: Parse existing InterProScan output file (format auto-detected from file extension)

### InterProScan Run Options (used with `--run`)

- `-i, --input FILE`: Input protein FASTA file (required)
- `-b, --output-base NAME`: Output file basename (optional, default: basename of input file)
  - InterProScan will append the format extension (e.g., `.tsv`, `.gff3`)
  - Example: `-b myanalysis` with `-f TSV` creates `myanalysis.tsv`
- `-f, --format {TSV,XML,JSON,GFF3}`: Output format (default: TSV)
- `--cpu N`: Number of CPUs to use (default: 4)
- `--databases DB`: Databases to search (default: all, or comma-separated list)
- `--pathways`: Include pathway annotations (optional)

**Note**: `--iprlookup` and `--goterms` are **always included by default** when running InterProScan. This ensures GO term annotations and InterPro mappings are always available in the output.

### Analysis Options

- `--longest-domain`: Select only the longest domain for each protein
- `--domain-stats FILE`: Output file for domain length distribution (JSON)
  - Default (with `--longest-domain`): `<basename>_domain_distribution.json`
- `--domain-stats-tsv FILE`: Output file for domain length distribution (TSV)
  - Default (with `--longest-domain`): `<basename>_domain_distribution.tsv`
- `--output-parsed FILE`: Output file for parsed results (JSON, optional)
- `--output-parsed-tsv FILE`: Output file for parsed results (TSV)
  - Default (without `--longest-domain`): `<basename>_parsed.tsv`
  - Default (with `--longest-domain`): `<basename>_longest_domains.tsv`

**Note**:
- `<basename>` refers to the InterProScan output file's basename (determined by `-b` option or input file)
- Default output format is **TSV** (matches InterProScan format)
- When `--longest-domain` is used without any output arguments, all output files are automatically generated with descriptive names
- Use `--output-parsed` to also generate JSON output if needed
- **All output files use the same basename** for consistent file organization

## TSV Format

### Input Format (InterProScan Standard - 15 columns)

InterProScan outputs a 15-column TSV format:

1. Protein accession (e.g., P51587)
2. Sequence MD5 digest (e.g., 14086411a2cdf1c4cba63020e1622579)
3. Sequence length (e.g., 3418)
4. Analysis/Database (e.g., Pfam, PRINTS, Gene3D)
5. Signature accession (e.g., PF09103, G3DSA:2.40.50.140)
6. Signature description (e.g., BRCA2 repeat profile)
7. Start location
8. Stop location
9. Score - e-value or score from database method (e.g., 3.1E-52)
10. Status - match status (T: true)
11. Date - run date
12. InterPro accession (e.g., IPR002093) - **may be "-" if no InterPro mapping**
13. InterPro description (e.g., BRCA2 repeat) - **may be "-"**
14. GO annotations (e.g., GO:0005515|GO:0006302) - **may be "-"**
15. Pathway annotations (e.g., REACT_71|MetaCyc:PWY-123) - **may be "-"**

**Note**: Missing values are represented as "-" (dash character).

### Output Format (This Tool - 14 columns)

This tool outputs a **14-column** TSV format:
- **Columns 1-13**: Standard InterProScan fields (same as input)
- **Column 14**: GO annotations (included if present in input)
- **Column 15 (Pathway annotations)**: **EXCLUDED from output TSV**

**Why exclude pathways?**
- Pathway annotations are stored internally in `self.pathway_annotations` dictionary for future programmatic use
- GO annotations are more commonly used for functional analysis and are retained
- This reduces file size and focuses on essential annotation data

**Accessing pathway data**: Pathway annotations are available in the JSON output or can be accessed programmatically via the `InterProParser.pathway_annotations` dictionary (format: `{protein_signature: pathway_value}`)

## Output Examples

### Parsed Results JSON

```json
[
  {
    "protein_accession": "P51587",
    "md5_digest": "14086411a2cdf1c4cba63020e1622579",
    "sequence_length": 3418,
    "analysis": "Pfam",
    "signature_accession": "PF09103",
    "signature_description": "BRCA2 repeat profile",
    "start_location": 100,
    "stop_location": 250,
    "score": "3.1E-52",
    "status": "T",
    "date": "2023-11-30",
    "interpro_accession": "IPR002093",
    "interpro_description": "BRCA2 repeat"
  }
]
```

### Domain Statistics JSON

```json
{
  "P51587": [
    {
      "domain": "BRCA2 repeat profile",
      "length": 151,
      "score": "3.1E-52",
      "start": 100,
      "stop": 250
    },
    {
      "domain": "DNA binding domain",
      "length": 98,
      "score": "1.2E-30",
      "start": 500,
      "stop": 597
    }
  ]
}
```

### Domain Statistics TSV

The TSV format includes a header row and the following columns:

```
protein_accession	domain_name	domain_length	score	start	stop	rank
P51587	BRCA2 repeat profile	151	3.1E-52	100	250	1
P51587	DNA binding domain	98	1.2E-30	500	597	2
```

Where `rank` indicates the domain order (1 = longest, 2 = second longest, etc.)

## Longest Domain Function

When a single protein matches multiple domains, the `--longest-domain` option:

1. Calculates domain coverage: `stop_location - start_location + 1`
2. Selects the longest domain for each protein (from any database)
3. Selects the longest **InterPro-annotated** domain for each protein (only IPR entries)
4. Generates distribution tables with all domain lengths for both sets

### Why Two Sets of Outputs?

InterProScan integrates results from multiple databases (Pfam, PRINTS, Gene3D, etc.). Sometimes:
- The **overall longest domain** comes from a database like Pfam
- The **longest InterPro-annotated domain** (with IPR accession) may be different

**Example scenario**:
```
Protein XYZ:
  - Pfam domain: 300 amino acids (longest overall)
  - InterPro IPR000123: 250 amino acids (longest with IPR annotation)
```

The regular output (`longest_domains`) contains the 300aa Pfam domain, while the `_NotintAnn` output contains the 250aa InterPro domain. This allows you to:
- Use overall longest for general domain architecture
- Use InterPro-specific for functional annotation and GO terms

This is useful for downstream analysis where you want a single representative domain per protein.

## Examples

### Complete Workflow

```bash
# Step 1: Run InterProScan with custom basename
# Note: --iprlookup and --goterms are included by default
python parse_interproscan.py \
    --run \
    --input my_proteins.fasta \
    --output-base my_analysis \
    --format TSV \
    --cpu 8 \
    --pathways
# Creates: my_analysis.tsv

# Step 2: Parse and analyze (export to both JSON and TSV)
python parse_interproscan.py \
    --parse my_analysis.tsv \
    --longest-domain \
    --domain-stats domain_stats.json \
    --domain-stats-tsv domain_stats.tsv \
    --output-parsed final_results.json \
    --output-parsed-tsv final_results.tsv

# Or use default basename (simpler):
python parse_interproscan.py \
    --run \
    --input my_proteins.fasta \
    --cpu 8 \
    --pathways
# Creates: my_proteins.tsv (automatically uses input basename)
```

### Parse Multiple Format Types

All formats are automatically detected from file extension:

```bash
# Parse TSV (auto-detected from .tsv extension)
python parse_interproscan.py --parse results.tsv

# Parse XML (auto-detected from .xml extension)
python parse_interproscan.py --parse results.xml

# Parse JSON (auto-detected from .json extension)
python parse_interproscan.py --parse results.json

# Parse GFF3 (auto-detected from .gff3 extension)
python parse_interproscan.py --parse results.gff3
```

**Supported Extensions**:
- `.tsv`, `.txt` → TSV format
- `.xml` → XML format
- `.json` → JSON format
- `.gff`, `.gff3` → GFF3 format

## Implementation Details

### Automatic Format Detection

The script automatically detects input file format based on file extension:

| Extension | Detected Format |
|-----------|----------------|
| `.tsv`, `.txt` | TSV |
| `.xml` | XML |
| `.json` | JSON |
| `.gff`, `.gff3` | GFF3 |
| Other extensions | TSV (default) |

The detected format is displayed when parsing begins.

### Basename Chaining

**All output files use a consistent basename** determined by:
1. **`--run` mode**: Uses `-b/--output-base` if provided, otherwise uses input file's basename
2. **`--parse` mode**: Uses the parsed file's basename

**Example 1: Run mode with default basename**
```bash
python parse_interproscan.py --run -i proteins.fasta --longest-domain
```
- Input basename: `proteins` (from `proteins.fasta`)
- InterProScan output: `proteins.tsv`
- All derivative outputs: `proteins_*.{json,tsv}`

**Example 2: Run mode with custom basename**
```bash
python parse_interproscan.py --run -i proteins.fasta -b experiment_v1 --longest-domain
```
- Custom basename: `experiment_v1`
- InterProScan output: `experiment_v1.tsv`
- All derivative outputs: `experiment_v1_*.{json,tsv}`

**Example 3: Parse mode**
```bash
python parse_interproscan.py --parse analysis.tsv --longest-domain
```
- Parse file basename: `analysis`
- All outputs: `analysis_*.{json,tsv}`

### Automatic Filename Generation

When output filenames are not explicitly provided, the script automatically generates descriptive filenames based on the basename:

| Scenario | Output Files Generated |
|----------|------------------------|
| Simple parsing | `<basename>_parsed.tsv` (default: TSV format) |
| With `--longest-domain` | **Overall longest** (any database):<br>`<basename>_longest_domains.json`<br>`<basename>_longest_domains.tsv`<br>`<basename>_domain_distribution.json`<br>`<basename>_domain_distribution.tsv`<br>**InterPro-annotated** (IPR only):<br>`<basename>_longest_domains_NotintAnn.json`<br>`<basename>_longest_domains_NotintAnn.tsv`<br>`<basename>_domain_distribution_NotintAnn.json`<br>`<basename>_domain_distribution_NotintAnn.tsv` |

**Examples**:
- Basename: `results` → Output: `results_parsed.tsv` (TSV is default)
- Basename: `proteins` with `--longest-domain` → Outputs (8 files total):
  - Overall longest: `proteins_longest_domains.{json,tsv}`, `proteins_domain_distribution.{json,tsv}`
  - InterPro only: `proteins_longest_domains_NotintAnn.{json,tsv}`, `proteins_domain_distribution_NotintAnn.{json,tsv}`

### TSV Export (No External Dependencies)

The TSV export functions use native Python string operations without the csv module:
- All values are converted to strings using `str()`
- Columns are joined with tab character (`\t`)
- Each row is written with newline (`\n`)
- Dash ("-") values from input are converted to empty strings
- No external libraries required

This ensures maximum portability and minimal dependencies.

### Handling Missing Values

**Input**: InterProScan uses "-" (dash) for missing values
**Processing**: Dashes are converted to empty strings during parsing
**Output TSV**: Missing values are output as empty strings (not dashes)
**JSON output**: Missing values are omitted from the dictionary (keys not present if empty)

## Notes

- File format is automatically detected from file extension (see supported extensions above)
- If file extension is not recognized, TSV format is assumed as default
- The XML and JSON parsers handle the standard InterProScan output structure
- Domain statistics are only generated when `--longest-domain` is used
- The script provides a summary of matches by database at the end
- TSV outputs use native Python - no csv module dependency
