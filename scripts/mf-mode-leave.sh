# Switch to the pass through cache mode
sudo casadm -Q -i 1 -c pt

# Stop the kernel monitor thread
sudo casadm -N

# List casadm to make sure
sudo casadm -L

