#!/bin/bash -l
#SBATCH -J protenix_predict
#SBATCH -o protenix_predict_%A.out
#SBATCH -p gpu
#SBATCH --ntasks=1
#SBATCH -c 8
#SBATCH --gres=gpu:1
#SBATCH -t 2-00:00:00
#SBATCH --mail-user=username@liverpool.ac.uk
#SBATCH --mail-type=ALL
#SBATCH --nodelist=compute31

# =========================
# Environment setup
# =========================

# Load Python module (if required by your cluster)
module load python/3.10

# Activate Conda environment
HOME="/home/sadikm/hc-storage"
source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate protenix_env

# Make sure CUDA ops are not rebuilt
export DS_BUILD_OPS=0

# Point to local Protenix cache (weights + CCD data)
export PROTENIX_CACHE=/home/shahmes/protenix_cache

# =========================
# Debug checks
# =========================
#echo "PROTENIX_CACHE = $PROTENIX_CACHE"
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); \
           print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"

#echo "Checkpoint files:"
ls -lh $PROTENIX_CACHE/checkpoint/

#echo "CCD cache files:"
ls -lh $PROTENIX_CACHE/ccd_cache/

# =========================
# Run Protenix
# =========================
start_time=$(date +%s)

protenix predict \
    --input ./test.json \
    --out_dir ./test3_protenix \
    --seeds 101 \
    --model_name "protenix_mini_esm_v0.5.0" \
    --use_msa false \
    --sample 1
start_time=$(date +%s)

end_time=$(date +%s)
runtime=$((end_time - start_time))
hours=$((runtime / 3600))
minutes=$(((runtime % 3600) / 60))
seconds=$((runtime % 60))
echo "Total runtime: ${hours}h ${minutes}m ${seconds}s"