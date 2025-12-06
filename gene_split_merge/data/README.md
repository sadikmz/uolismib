# Data Directory

## Purpose

Place your input genome annotation and protein files here.

## Required Files

### For Standard Workflow

Place these 4 files in this directory:

1. **reference.gff3** - Reference genome annotation (GFF3 format)
2. **reference_proteins.fasta** - Reference protein sequences (FASTA)
3. **updated.gff3** - Updated genome annotation (GFF3 format)
4. **updated_proteins.fasta** - Updated protein sequences (FASTA)

### For Enhanced Workflow (Additional)

If using the enhanced workflow with assembly validation, also include:

5. **reference_genome.fasta** - Reference genome assembly (FASTA)
6. **updated_genome.fasta** - Updated genome assembly (FASTA)

## File Format Requirements

### GFF3 Files
- Must have `gene` features with `ID=` attributes
- Standard GFF3 format
- Can be generated from genome annotation pipelines

### Protein FASTA Files
- Protein IDs must match gene IDs in GFF3 files
- Standard FASTA format
- One sequence per gene

### Genome FASTA Files (Enhanced workflow only)
- Genome assembly sequences
- Standard FASTA format
- Used for assembly quality validation

## Example File Names

You can use any filenames, but specify them on the command line:

```bash
cd ../bin
python3 detect_gene_split_merge.py \
    --ref-gff ../data/my_reference.gff3 \
    --ref-proteins ../data/my_ref_proteins.faa \
    --upd-gff ../data/my_updated.gff3 \
    --upd-proteins ../data/my_upd_proteins.faa \
    --output ../results/
```

## File Size Considerations

- Small genomes (<10k genes): ~10-50 MB total
- Medium genomes (20k genes): ~50-200 MB total
- Large genomes (50k genes): ~200-500 MB total

Ensure you have sufficient disk space for:
- Input files (in this directory)
- DIAMOND databases (~2x protein file size)
- Alignment results (~1-5x protein file size)

## Notes

- Keep files compressed (.gz) during storage if needed
- Decompress before analysis
- Files should be from the same organism/individual
- Reference and updated should be different assemblies/annotations of the same genome
