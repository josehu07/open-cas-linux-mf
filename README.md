# Open CAS Linux - Guanzhou's Fork

This is Guanzhou's fork of Intel's Open-CAS Linux cache accelaration system.


## Overview

Folder structure:

```text
# This is the `casadm` CLI management tool.
# Added `-M` & `-N` command options and `mfwa|mfwb|mfwt` cache modes.
casadm/
 |- cas_main.c
 |- cas_lib.c
 |- cas_lib.h
 |- ...
```

```text
# These are CAS kernel modules loaded into the kernel, i.e., the Linux context.
# New commands support added here.
modules/
 |- cas_cache/  # This is the `cas_cache` ko, Linux control cdev also implemented here
 |   |- service_ui_ioctl.c
 |   |- layer_cache_management.c
 |   |- ...
 |- cas_disk/   # This is the `cas_disk` core device ko
 |- include/
 |   | cas_ioctl_codes.h
 |- ...
```

```text
# This is the OCF.
# MFC plugins ported to use Linux kernel headers only.
ocf/
 |- ...
```

Everything I have added/modified are marked by `[Orthus FLAG BEGIN]` and `[Orthus FLAG END]` for easier future reference.


## Usage

Tested on the following platforms:

- Ubuntu 18.04 LTS

Clone the repo recursively (there is a submodule - the OCF framework):

```bash
$ git clone --recursive git@github.com:josehu07/open-cas-linux-mf.git
$ cd open-cas-linux-mf
$ git submodule update --init --recursive
```

### Install Open-CAS-Linux

Make sure you have full Linux kernel headers installed.

At the top-level folder, compile by:

```bash
$ sudo ./configure
$ make
```

Then, install by:

```bash
$ sudo make install
```

Check your installation is successful:

```bash
$ sudo casadm -V
```

### Setting Up an MFC Cache

Once installed, you can set up Open-CAS to start a cache on a device, add another device as a core to the cache, and then mount the virtual `/dev/casX-Y` block device to some path.

First, be sure to format the core device to desired FS type:

```bash
$ sudo mkfs.ext4 /dev/yyy
```

Start the cache and add a core:

```bash
$ sudo casadm -S -d /dev/xxx            # Start cache in WT mode as cache_id = 1
$ sudo casadm -A -d /dev/yyy -i 1       # Add a core device to cache 1
$ sudo casadm -L                        # List current CAS status
```

Take a look at `open-cas-linux-mf/ocf/src/engine/mf_monitor.c`. Edit monitor parameters and block device stat file path according to your setup.

```C
/** Enable kernel verbose logging? */
static const bool MONITOR_VERBOSE_LOG = true;


/** For block device throughput measurement. */
static const char *CACHE_STAT_FILENAME = "/sys/block/sdc/stat";
static const char *CORE_STAT_FILENAME  = "/sys/block/sdb/stat";


/** Do not attempt tuning when miss ratio is higher than X. */
static const int MISS_RATIO_TUNING_BOUND = 2000;    // 20%.

/** Consider cache is stable if miss ratio within OLD_RATIO +- X. */
static const int WAIT_STABLE_THRESHOLD = 10;        // 0.1%.

/** Sleep X microseconds when detecting cache stability. */
static const int WAIT_STABLE_SLEEP_INTERVAL_US = 1000000;

/** Consider workload change when miss ratio > BASE_RATIO + X. */
static const int WORKLOAD_CHANGE_THRESHOLD = 2000;  // 20%.

/** `load_admit` tuning step size. */
static const int LOAD_ADMIT_TUNING_STEP = 100;      // 1%.

/** Measure throughput for a `load_admit` value for X microseconds. */
static const int MEASURE_THROUGHPUT_INTERVAL_US = 5000;

/** How many chances given to not quit on `load_admit` 100%. */
static const int NOT_QUIT_ON_100_CHANCES = 10;
```

Then, start the monitor and switch the cache to a multi-factor cache mode, for example `mfwa`:

```bash
$ sudo casadm -M -i 1 -j 1              # Start multi-factor monitor to monitor core 1-1
$ sudo casadm -Q -i 1 -c mfwa           # Switch cache 1 to Multi-Factor Write-Around
```

Verify that the cache mode has changed:

```bash
$ sudo casadm -L
```

Now, you can mount the virtual CAS device to a path and starting using Open-CAS-Linux:

```bash
$ sudo mount /dev/cas1-1 /mnt/some_path
```

### Terminating an MFC Cache

**IMPORTANT**: You should **first switch the cache to non-mf mode and stop the monitor**. Otherwise, directly unmounting or terminating the cache will make your kernel stuck. Do this by:

```bash
$ sudo casadm -Q -i 1 -c pt             # Swtich cache 1 to Pass-Through mode
$ sudo casadm -N                        # Stop the running multi-factor monitor
```

Unmount the virtual device:

```bash
$ sudo umount /mnt/some_path
```

Then, terminate the cache:

```bash
$ sudo casadm -T -i 1                   # Terminate cache 1
```

Make sure that no cache is now running:

```bash
$ sudo casadm -L
```

> You will find the scripts under `open-cas-linux-mf/scripts` useful. Make sure to check their contents and set correct block device pathes on your system. They are almost certainly different from what's on my node.


## Original README

[![Build Status](https://open-cas-logs.s3.us-east-2.amazonaws.com/master-status/ocl/build/curr-badge.svg)](https://open-cas-logs.s3.us-east-2.amazonaws.com/master-status/ocl/build/build.html)
[![Tests Status](https://open-cas-logs.s3.us-east-2.amazonaws.com/master-status/ocl/tests/curr-badge.svg)](https://open-cas-logs.s3.us-east-2.amazonaws.com/master-status/ocl/tests/tests.html)
[![Coverity status](https://scan.coverity.com/projects/19084/badge.svg)](https://scan.coverity.com/projects/open-cas-open-cas-linux)
[![License](https://open-cas-logs.s3.us-east-2.amazonaws.com/master-status/license-badge.svg)](LICENSE)

Open CAS  accelerates Linux applications by caching active (hot) data to
a local flash device inside servers. Open CAS implements caching at the
server level, utilizing local high-performance flash media as the cache drive
media inside the application server as close as possible to the CPU, thus
reducing storage latency as much as possible.
The Open Cache Acceleration Software installs into the GNU/Linux operating
system itself, as a kernel module. The nature of the integration provides a
cache solution that is transparent to users and  applications, and your
existing storage infrastructure. No storage migration effort or application
changes are required.

Open CAS is distributed on BSD-3-Clause license (see
https://opensource.org/licenses/BSD-3-Clause for full license texts).

Open CAS uses Safe string library (safeclib) that is MIT licensed.

### Installation

To download latest Open CAS Linux release run following commands:

```
wget https://github.com/Open-CAS/open-cas-linux/releases/download/v20.3/open-cas-linux-v20.03.0.0286.tar.gz
tar -xf open-cas-linux-v20.03.0.0286.tar.gz
cd open-cas-linux-v20.03.0.0286/
```

Alternatively, if you want recent development (unstable) version, you can clone GitHub repository:

```
git clone https://github.com/Open-CAS/open-cas-linux
cd open-cas-linux
git submodule update --init
```

To configure, build and install Open CAS Linux run following commands:

```
./configure
make
make install
```

The `./configure` performs check for dependencies, so if some of them are missing,
command will print their names in output. After installing missing dependencies
you need to run `./configure` once again - this time it should succeed.

### Getting Started

To quickly deploy Open CAS Linux in your system please follow the instructions
available [here](https://open-cas.github.io/getting_started_open_cas_linux.html).

### Documentation

The complete documentation for Open CAS Linux is available in the
[Open CAS Linux Administration Guide](https://open-cas.github.io/guide_introduction.html).

### Running Tests

Before running tests make sure you have a platform with at least 2 disks (one for cache and one for core). Be careful as these devices will be most likely overwritten with random data during tests. Tests can be either executed locally or on a remote platform (via ssh) specified in the dut_config.

1. Go to test directory `cd test/functional`.
1. Install dependencies with command `pip3 install -r test-framework/requirements.txt`.
1. Create DUT config. See example [here](test/functional/config/example_dut_config.yml).  
    a) Set disks params. You need at least two disks, of which at least one is an SSD drive.  
    b) For remote execution uncomment and set the `ip`, `user` and `password` fields.  
    c) For local execution just leave these fields commented.
1. Run tests using command `pytest-3 --dut-config=<CONFIG>` where `<CONFIG>` is path to your config file, for example `pytest-3 --dut-config="config/dut_config.yml"`.

### Security

To report a potential security vulnerability please follow the instructions
[here](https://open-cas.github.io/contributing.html#reporting-a-potential-security-vulnerability).
