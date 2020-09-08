casadm -N
casadm -T -i 1


casadm -S -d /dev/nvme1n1p1 -x 64  --force
casadm -A -d /dev/nvme0n1 -i 1
casadm -X -n seq-cutoff -i 1  -p never



sudo casadm -M -i 1 -j 1
sudo casadm -Q -i 1 -c mfwa


fio randread_ram_small.fio
