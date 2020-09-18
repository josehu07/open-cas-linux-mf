
#!/bin/bash

if [[ $# -ne 2 ]]; then
    echo "Please provide two arguments: the cache mode, T(the time us we change the read ratio)"
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
# to use SIB
#sudo casadm -M -i 1 -j 1 -m tl
sudo casadm -Q -i 1 -c $1 

# Optane SSD
make multi_thread_aio_dynamic ; ./multi_thread_aio_dynamic /dev/cas1-1 $2 2 128 16

# NVDIMM
#make multi_thread_aio ; ./multi_thread_aio /dev/cas1-1 $2 8 128 $3 $4

dmesg --clear
