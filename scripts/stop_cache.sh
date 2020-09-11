#!/bin/bash
sudo casadm -Q -i 1 -c pt
sudo casadm -N
sudo umount /mnt/tmpfs
sudo casadm -T -i 1
sudo casadm -L
