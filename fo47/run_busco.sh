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

## activate the specific env to run
conda activate "$miniconda"/envs/busco


# Set variables
cwd=$(pwd)
# threads=31
tmp="/dev/shm"
# mem=150
genotype="GCF_013085055.1"
DATADIR="$HOME/data"
ref_genome="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_Genome.fasta"
ref_gff="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47.gff"
ref_prot="$DATADIR/foc47/v68/FungiDB-68_FoxysporumFo47_AnnotatedProteins.fasta"

target_genome=$DATADIR/foc47/$genotype/"$genotype"_ASM1308505v1_genomic.fna
APPSDIR=/home/sadikm/hc-storage/apps

# list of 

# Run liftoff process liftover files 
echo "$genotype"_liftover.gff3_polished > input_gff

# Run gffcompare

gffcompare \
-i input_gff \
-o foc47_vs_"$genotype"_gffcomp \
-r "$ref_gff" \
-p foc47_vs_"$genotype"_TCONS

