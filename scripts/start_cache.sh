#!/bin/bash
sudo casadm -S --load -d /dev/sdc            # Start cache in WT mode as cache_id = 1
# sudo casadm -A -d /dev/sdb -i 1       # Add a core device to cache 1
sudo casadm -L                        # List current CAS status
sudo casadm -M -i 1 -j 1 -m tl
sudo casadm -Q -i 1 -c mfwa
sudo casadm -L

sudo mount /dev/cas1-1 /mnt/tmpfs
