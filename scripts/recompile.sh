sudo umount /mnt/casdir

sudo casadm -N
sudo casadm -T -i 1

sudo make uninstall
make clean

make
sudo make install
