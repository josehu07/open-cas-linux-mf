# Create a ramdisk of 16GiB at /dev/loop0.
sudo mkdir /ramdisk
sudo mount -t tmpfs tmpfs /ramdisk
sudo dd if=/dev/zero of=/ramdisk/loopfile bs=1G count=16
sudo losetup /dev/loop0 /ramdisk/loopfile

# Format the ramdisk block device as EXT4.
sudo mkfs.ext4 /dev/loop0

