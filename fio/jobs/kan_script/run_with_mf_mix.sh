#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo "Please provide one argument: the mf cache mode"
    exit 1
fi

if [[ $1 -ne mfwa ]] && [[ $1 -ne mfwb ]] && [[ $1 -ne mfwt ]]; then
    echo "Unrecognized mf cache mode: $1"
    exit 2
fi

casadm -N
casadm -T -i 1

# Optane SSD as cache
casadm -S -d /dev/nvme1n1p1 -x 64  --force

# NVDIMM as cache
#casadm -S -d /dev/pmem0p1 -x 64  --force

# DRAM as cache
#casadm -S -d /dev/ram0 -x 64  --force




# Flash SSD as core
casadm -A -d /dev/nvme0n1 -i 1

# Optane SSD as core
#casadm -A -d /dev/nvme1n1 -i 1

# NVDIMM as core
#casadm -A -d /dev/pmem0 -i 1



casadm -X -n seq-cutoff -i 1  -p never
sudo casadm -M -i 1 -j 1
sudo casadm -Q -i 1 -c $1 


make multi_thread_aio ; ./multi_thread_aio /dev/cas1-1 50 2 128 100 8

dmesg --clear