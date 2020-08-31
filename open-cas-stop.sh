# Stop CAS cache.
echo "\nStopping CAS cache #1...\n"
sudo casadm -T -i 1

# List CAS status to make sure.
echo "\nListing CAS status (casadm -L)...\n"
sudo casadm -L

# List block devices to see /dev/casX-Y device shows up.
echo "\nListing block devices (lsblk)...\n"
lsblk
