# downlaod data
# "$APPSDIR"/datasets download genome accession "$genotype" --include protein,gff3,cds,rna,genome

## Load bash_profile to avail to tools appeneded in the $PATH. HOME set to "/home/sadikm/hc-storage"
source /home/sadikm/.bashrc

# for some reason (for new prog path in $HOME/apps), need to load bash_profile too
source /home/sadikm/.bash_profile

## When using conda installation 
# Load Miniconda3 module if exists in the HPC system
# module load Miniconda3/version.....

## conda base environment
HOME="/home/sadikm/hc-storage"
miniconda="$HOME/miniconda3"
source "$miniconda"/bin/activate

# downlaod data
# "$APPSDIR"/datasets download genome accession "$genotype" --include protein,gff3,cds,rna,genome

# Set variables
cwd=$(pwd)
threads=40
tmp="/dev/shm"
# mem=150
genotype="GCF_013085055.1"
DATADIR="/home/sadikm/hc-storage/data"
ref_genome="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_Genome.fasta"
ref_gff="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47.gff"
ref_prot="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_AnnotatedProteins.fasta"

target_genome=$DATADIR/foc47/$genotype/"$genotype"_ASM1308505v1_genomic.fna
APPSDIR=/home/sadikm/hc-storage/apps

# Run liftoff process liftover files 

# liftoff \
# "$target_genome" \
# "$ref_genome" \
# -g "$ref_gff" \
# -o "$genotype"_liftover.gff3 \
# -u "$genotype"_liftover_unmapped_features.txt \
# -exclude_partial \
# -dir intermiate_dir \
# -copies \
# -polish \
# -cds \
# -f feature_type_list.txt


# Extract transcript IDs of liftover annotation 
# cat "$genotype"_liftover.gff3_polished | grep -E 'CDS' | cut -f9  | sed 's/ID=//g' | sed 's/-CDS.*//g' | sort | uniq > "$genotype"_liftover.gff3_polished_transcript_ids.txt

# Tidy up protein sequence IDs to match with transcript IDs of the liftover annotation
ref_prot_basename=$(basename "$ref_prot" .fasta) 
# cat "$ref_prot" | sed 's/|.*//g' | sed 's/^[[:space:]]*//g' | sed 's/>//g' > "$ref_prot_basename".01.fasta

# Get protein sequences of liftover annotation 

# seqtk subseq "$ref_prot_basename".01.fasta "$genotype"_liftover.gff3_polished_transcript_ids.txt > "$genotype"_liftover_polished_protein.fa
seqtk --help > test_seqtk_help.txt

# Run BUSCO
## activate the specific env to run
conda activate "$miniconda"/envs/busco
busco_path=$(which busco)

# compleasm_output_dir="$BASENAME"_compleasm.out
dowloaded_lineage_path=compleasm_lineage_dir
mode=

# BUSCO: selected lineages - distal to closest to Foc
# lineage_list.txt
    # eukaryota_odb12
    # fungi_odb12
    # ascomycota_odb12
    # hypocreales_odb12
    # nectriaceae_odb12

mkdir busco_results
cp foc_lineages_list.txt busco_results/
cd busco_results
busco --help > test_busco_help.txt
"$busco_path" --help > test_busco_help.txt

# for lineage in $(cat foc_lineages_list.txt); do
#     echo "Running BUSCO for lineage: $lineage"
#     busco \
#     -i ../"$genotype"_liftover_polished_protein.fa  \
#     -m protein  \
#     -l $lineage \
#     -c $threads \
#     -o "$genotype"_"$lineage"_busco.out \
#     --miniprot \
#     --long \
#     --tar \
#     --force
# done


    # 
    # 
    # 
    # 
