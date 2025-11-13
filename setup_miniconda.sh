!/bin/bash

# Set-up a local mniconda installation

# source: https://www.anaconda.com/docs/getting-started/miniconda/install#linux-2 

HOME=/home/sadikm/hc-storage

mkdir -p $HOME/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O $HOME/miniconda3/miniconda.sh
bash $HOME/miniconda3/miniconda.sh -b -u -p $HOME/miniconda3
rm $HOME/miniconda3/miniconda.sh

source miniconda3/bin/activate

# Configure conda channels
conda config --add channels bioconda
conda config --add channels conda-forge
conda config --set channel_priority strict
