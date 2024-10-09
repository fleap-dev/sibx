# Evaluation Scripts
This directory contains the evaluation scripts for the paper.

A reproducible container image can be built and run by executing these commands:
```bash
docker build -t sib:evaluation .. -f Dockerfile
docker run --rm -v /path/to/outputdir:/data:Z sib:evaluation
```
This container runs three different experiments for Linux, OpenSSL, SQLite, and Bochs. The results are written as CSV files in the linked directory. The experiments are called:

- WOP
    - Short for "**w**ith**o**ut **p**atch check". This is referred to as the binary equivalence-based approach in the paper. There is no "prediction"; this approach simply compares compiled programs and is used as ground truth.
- WOP+CCache
    - This adds Ccache to the WOP experiment to increase build speed.
- MPC
   - This is referred to as SiB in the paper.
