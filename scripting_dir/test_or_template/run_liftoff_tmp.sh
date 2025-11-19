# downlaod data
"$APPSDIR"/datasets download genome accession "$genotype" --include protein,gff3,cds,rna,genome

# Set variables
cwd=$(pwd)
threads=31
tmp="/dev/shm"
mem=150
genotype="GCF_013085055.1"
DATADIR="/home/sadikm/hc-storage/data"
ref_genome="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_Genome.fasta"
ref_gff="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47.gff"
ref_prot="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_AnnotatedProteins.fasta"

target_genome=$DATADIR/foc47/$genotype/"$genotype"_ASM1308505v1_genomic.fna
APPSDIR=/home/sadikm/hc-storage/apps


# Run liftoff

liftoff \
"$target_genome" \
"$ref_genome" \
-g "$ref_gff" \
-o "$genotype"_liftover.gff3 \
-u "$genotype"_liftover_unmapped_features.txt \
-exclude_partial \
-dir intermiate_dir \
-copies \
-polish \
-cds \
-f feature_type_list.txt

# remote tmp dir
# rm -rf "$TMPDIR"

# Extract transcript IDs of liftover annotation 
cat "$genotype"_liftover.gff3_polished | grep -E 'CDS' | cut -f9  | sed 's/ID=//g' | sed 's/-CDS.*//g' | sort | uniq > "$genotype"_liftover.gff3_polished_transcript_ids.txt

# Filter out multicopy genes / probably false duplication/

# cat "$genotype"_liftover.gff3_polished_ids.txt | grep -v '_' > "$genotype"_liftover.gff3_polished_ids.txt.01.txt

# Extract transcript IDs of reference annotation
ref_gff_basename=$(basename "$ref_gff" .gff) 
# grep '>' "$ref_prot" | sed 's/>//g' > "$ref_gff_basename"_transcript_ID_list.txt

grep '>' "$ref_prot" | sed 's/|.*//g' | sed 's/^[[:space:]]*//g' | sed 's/>//g' > "$ref_gff_basename"_transcript_ID_list.txt

# subset liftover annotation transcript IDs list from reference annoation 
grep -f "$genotype"_liftover.gff3_polished_transcript_ids.txt "$genotype"_v5.6_annotation_transcript_ID_list.txt > "$genotype"_liftover.gff3_polished_ids.txt.02.txt


# Load seqtk 
module load seqtk/1.3-foss-2018a

seqtk subseq "$ref_prot" "$genotype"_liftover.gff3_polished_ids.txt.02.txt > "$genotype"_liftover_polished_protein.fa

# Run BUSCO

BASENAME=$genotype
#BASENAME=NWC665
#genotype=chlamydomonas_reinhardtii
busco_output_dir="$BASENAME"_busco.out
compleasm_output_dir="$BASENAME"_compleasm.out
lineage=chlorophyta_odb10
mode=genome
dowloaded_lineage_path=compleasm_lineage_dir
mode=

# BUSCO

busco \
-i "$genotype"_liftover_polished_protein.fa  \
-m protein  \
-l $lineage \
-c $threads \
-o $busco_output_dir \
--miniprot \
--long \
--tar \
--force


