#!/bin/bash
#SBATCH --job-name=fo47_lo 
#SBATCH --partition=med
#SBATCH --time=24-00:00:00
#SBATCH --mem=40G
#SBATCH --ntasks=1          
#SBATCH --cpus-per-task=40   
#SBATCH --output=job.%J.%N.out
#SBATCH --error=job.%J.%N.err
#SBATCH --mail-user=sadikm@liverpool.ac.uk
#SBATCH --mail-type=END,FAIL

# load module


## Load bash_profile to avail to tools appeneded in the $PATH. HOME set to "/home/sadikm/hc-storage"
# Activate Conda environment
HOME="/home/sadikm/hc-storage"
source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate busco


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
cat "$genotype"_liftover.gff3_polished | grep -E 'CDS' | cut -f9  | sed 's/ID=//g' | sed 's/-CDS.*//g' | sort | uniq > "$genotype"_liftover.gff3_polished_transcript_ids.txt

# Tidy up protein sequence IDs to match with transcript IDs of the liftover annotation
ref_prot_basename=$(basename "$ref_prot" .fasta) 
cat "$ref_prot" | sed 's/|.*//g' | sed 's/^[[:space:]]*//g' | sed 's/>//g' > "$ref_prot_basename".01.fasta

# Get protein sequences of liftover annotation 

seqtk subseq "$ref_prot_basename".01.fasta "$genotype"_liftover.gff3_polished_transcript_ids.txt > "$genotype"_liftover_polished_protein.fa

# Run BUSCO
## activate the specific env to run
conda activate "$miniconda"/envs/busco

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


mkdir busco_old_annot

for lineage in $(cat foc_BUSCO_lineages.txt); do
    echo "Running BUSCO for lineage: $lineage"
busco \
    -i "$ref_prot_basename".01.fasta  \
    -m protein  \
    -l "$lineage" \
    -c $threads \
    -o "$genotype"_"$lineage"_busco.bf.out \
    --offline \
    --tar 

    # add slurm job output files to busco_results dir
    mv busco_*.log "$genotype"_"$lineage"_busco.bf.out busco_results/
done

# add slurm job output files to busco_results dir
mv job.$SLURM_JOB_ID.$SLURM_JOBID.* busco_results/

mkdir busco_liftover_annot

for lineage in $(cat foc_BUSCO_lineages.txt); do
    echo "Running BUSCO for lineage: $lineage"
busco \
    -i "$genotype"_liftover_polished_protein.fa  \
    -m protein  \
    -l "$lineage" \
    -c $threads \
    -o "$genotype"_"$lineage"_busco.af.out \
    --offline \
    --tar 

    # add slurm job output files to busco_after dir
    mv busco_*.log "$genotype"_"$lineage"_busco.af.out busco_after/
done

# add slurm job output files to busco_after dir
mv job.$SLURM_JOB_ID.$SLURM_JOBID.* busco_after/

mkdir busco_new_ncbi_annot
for lineage in $(cat foc_BUSCO_lineages.txt); do
    echo "Running BUSCO for lineage: $lineage"
busco \
    -i "$genotype"_liftover_polished_protein.fa  \
    -m protein  \
    -l "$lineage" \
    -c $threads \
    -o "$genotype"_"$lineage"_busco.af.out \
    --offline \
    --tar 

    # add slurm job output files to busco_after dir
    mv busco_*.log "$genotype"_"$lineage"_busco.af.out busco_after/
done
