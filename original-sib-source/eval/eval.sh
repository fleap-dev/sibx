#!/usr/bin/env bash

NUM_COMMITS=200 # Modify to speed up the evaluation. Minimum: 2.
OPENSSL_VARIANTS=15
SQLITE_VARIANTS=15
LINUX_VARIANTS=15
BOCHS_VARIANTS=15

# Remove projects to speed up the evaluation.
projects=(
    linux
    openssl
    sqlite
    bochs
)

for project in "${projects[@]}"; do
    VERSION=${project^^}_VERSION
    VARIANTS=${project^^}_VARIANTS

    # alternative implementation based on object-file hashes
    /eval.py /${project} --commits ${!VERSION}...${!VERSION}~$(($NUM_COMMITS+2)) -m ${project}_wop.py -p /plugin.so -t /mpc --compiler "/usr/bin/$COMPILER" --dump-dir /data2/${project}_wop --num-variants ${!VARIANTS} --clean -o /data/${project}_wop.csv


    # alternative implementation based on object-file hashes + Ccache
    ccache --clear
    ccache --zero-stats
    /eval.py /${project} --commits ${!VERSION}...${!VERSION}~$(($NUM_COMMITS+2)) -m ${project}_ccache.py -p /plugin.so -t /mpc --compiler "/usr/lib/ccache/$COMPILER" --dump-dir /data2/${project}_ccache --num-variants ${!VARIANTS} --clean -o /data/${project}_wop_ccache.csv
    ccache --show-stats

    /eval.py /${project} --commits ${!VERSION}~...${!VERSION}~$(($NUM_COMMITS+2)) -m ${project}_wop_check.py -p /plugin.so -t /mpc --dump-dir /data2/${project}_ccache --num-variants ${!VARIANTS} -o /data/${project}_wop_check.csv

    # SiB
    /eval.py /${project} --commits ${!VERSION}...${!VERSION}~$(($NUM_COMMITS+2)) -m ${project}.py -p /plugin.so -t /mpc --compiler "/usr/bin/$COMPILER" --dump-dir /data2/${project} --num-variants ${!VARIANTS} --clean -o /data/${project}_mpc.csv

    /eval.py /${project} --commits ${!VERSION}~...${!VERSION}~$(($NUM_COMMITS+2)) -m ${project}_check.py -p /plugin.so -t /mpc --dump-dir /data2/${project} -o /data/${project}_mpc_check.csv
done
