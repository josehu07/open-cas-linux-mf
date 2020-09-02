DEV_CORE=/dev/disk/by-id/ata-INTEL_SSDSC2BB480G4_PHWL444303SP480QGN     # /dev/sdc
DEV_CACHE=/dev/loop0                                                    # Ramdisk block

# Format core device as EXT4 file system.
echo "\nFormatting core device...\n"
# sudo mkfs.ext4 ${DEV_CORE}

# Setup SSD device as CAS cache ID #1, using WT mode.
echo "\nStarting SSD as cache device #1, mode = wt...\n"
sudo casadm -S -i 1 -d ${DEV_CACHE} -c wt -f

# Attach HDD device to cache #1.
echo "\nAttaching HDD device to cache #1...\n"
sudo casadm -A -i 1 -d ${DEV_CORE}

# List CAS status to make sure.
echo "\nListing CAS status (casadm -L)...\n"
sudo casadm -L

# List block devices to see /dev/casX-Y device shows up.
echo "\nListing block devices (lsblk)...\n"
lsblk

