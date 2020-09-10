#!/bin/bash

if [[ $# -ne 2 ]]; then
    echo "Please provide two arguments: the mf cache mode, the fio job file"
    exit 1
fi

if [[ $1 -ne wa ]] && [[ $1 -ne wb ]] && [[ $1 -ne wt ]]; then
    echo "Unrecognized cache mode: $1"
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
sudo casadm -Q -i 1 -c $1 


fio $2 

dmesg --clear
