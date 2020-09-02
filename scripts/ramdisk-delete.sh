# Remove the ramdisk /dev/loop0 block device.
sudo losetup -d /dev/loop0
sudo rm /ramdisk/loopfile
sudo umount /ramdisk

