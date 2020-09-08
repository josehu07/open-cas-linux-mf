swapoff -a
casadm -N
casadm -T -i 1
make uninstall
make clean

#./configure
make
make install
