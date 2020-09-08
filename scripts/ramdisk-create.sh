# Create a ramdisk of 8GiB at /dev/ram0.
sudo modprobe brd rd_nr=1 rd_size=$((8 * 1048576))

