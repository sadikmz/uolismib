# downlaod data
"$APPSDIR"/datasets download genome accession "$genotype" --include protein,gff3,cds,rna,genome

# Set variables
cwd=$(pwd)
# threads=31
tmp="/dev/shm"
# mem=150
genotype="GCF_013085055.1"
DATADIR="/home/sadikm/hc-storage/data"
ref_genome="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_Genome.fasta"
ref_gff="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47.gff"
ref_prot="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_AnnotatedProteins.fasta"

target_genome=$DATADIR/foc47/$genotype/"$genotype"_ASM1308505v1_genomic.fna
target_gff=$DATADIR/foc47/$genotype/genomic.gff
target_prot=$DATADIR/foc47/$genotype/protein.faa

APPSDIR=/home/sadikm/hc-storage/apps

# list of 

# Run liftoff process liftover files 

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


# Run gffcompare liftover vs target gff 
gffcompare \
-i input_gff \
-o foc47_vs_"$genotype"_gffcomp \
-r "$target_gff" \
-p foc47_vs_"$genotype"_TCONS

