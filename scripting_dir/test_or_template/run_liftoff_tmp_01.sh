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

# Tidy up protein sequence IDs to match with transcript IDs of the liftover annotation
ref_prot_basename=$(basename "$ref_prot" .fasta) 
cat "$ref_prot" | sed 's/|.*//g' | sed 's/^[[:space:]]*//g' | sed 's/>//g' > "$ref_gff_basename".01.fasta

# Get protein sequences of liftover annotation 

seqtk subseq "$ref_gff_basename".01.fasta "$genotype"_liftover.gff3_polished_ids.txt.02.txt > "$genotype"_liftover_polished_protein.fa

# Run BUSCO
# BUSCO lineages for Fusarium oxysporum in literature: 
# - eukaryota_odb12 [129]
#     - amoebozoa_odb12 [434]
#     - fungi_odb12 [1122]
#         - basidiomycota_odb12 [2409]
#             - agaricomycetes_odb12 [3398]
#                 - boletales_odb12 [4126]
#                 - agaricales_odb12 [3408]
#                 - polyporales_odb12 [4690]
#                     - polyporaceae_odb12 [5977]
#             - tremellomycetes_odb12 [3477]
#             - ustilaginomycetes_odb12 [4941]
#             - pucciniomycetes_odb12 [3329]
#             - microbotryomycetes_odb12 [3077]
#         - ascomycota_odb12 [2826]
#             - sordariomycetes_odb12 [4492]
#                 - xylariales_odb12 [5708]
#                 - sordariales_odb12 [5603]
#                 - hypocreales_odb12 [4349]
#                     - hypocreaceae_odb12 [4323]
#                     - cordycipitaceae_odb12 [4122]
#                     - ophiocordycipitaceae_odb12 [4329]
#                     - clavicipitaceae_odb12 [4861]
#                     - nectriaceae_odb12 [5719]
                            # Foc sits here

BASENAME=$genotype
#BASENAME=NWC665
#genotype=chlamydomonas_reinhardtii
busco_output_dir="$BASENAME"_busco.out
compleasm_output_dir="$BASENAME"_compleasm.out
# lineage=eukaryota_odb12
mode=genome
dowloaded_lineage_path=compleasm_lineage_dir
mode=

# BUSCO: selected lineages - distal to closest to Foc
# lineage_list.txt
    # eukaryota_odb12
    # fungi_odb12
    # ascomycota_odb12
    # hypocreales_odb12
    # nectriaceae_odb12



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




