# Load the whole core device to cache (assuming cache cap > core)
sudo dd if=/dev/cas1-1 of=/dev/null bs=64K
