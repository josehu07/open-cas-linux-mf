# Switch SSD I/O scheduler to noop.
sudo bash -c 'echo noop > /sys/block/sdc/queue/scheduler'

