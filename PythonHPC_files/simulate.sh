#!/bin/bash
#BSUB -J jacobi
#BSUB -q hpc
#BSUB -W 20:00
#BSUB -R "rusage[mem=2GB]"
#BSUB -o %J.out
#BSUB -e %J.err
#BSUB -B 
#BSUB -N 
#BSUB -u s204201@dtu.dk
#BSUB -R "select[model == XeonGold6126]"
#BSUB -n 4 
#BSUB -R "span[hosts=1]"

# Activate your virtual environment
source /dtu/projects/02613_2024/conda/conda_init.sh
conda activate 02613

# Run the simulation for a small subset (10 floorplans) and time it.
time python simulate.py 10
