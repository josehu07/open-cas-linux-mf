#
# Copyright(c) 2019-2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#


import re
import time
from enum import Enum

from core.test_run import TestRun
from test_tools import fs_utils
from test_tools.dd import Dd
from test_utils.size import Size, Unit


class Filesystem(Enum):
    xfs = 0
    ext3 = 1
    ext4 = 2


class PartitionTable(Enum):
    msdos = 0
    gpt = 1


class PartitionType(Enum):
    efi = 0
    primary = 1
    extended = 2
    logical = 3
    lvm = 4
    msr = 5
    swap = 6
    standard = 7
    unknown = 8


def create_filesystem(device, filesystem: Filesystem, force=True, blocksize=None):
    TestRun.LOGGER.info(
        f"Creating filesystem ({filesystem.name}) on device: {device.system_path}")
    force_param = ' -f ' if filesystem == Filesystem.xfs else ' -F '
    force_param = force_param if force else ''
    block_size_param = f' -b size={blocksize}' if filesystem == Filesystem.xfs \
        else f' -b {blocksize}'
    block_size_param = block_size_param if blocksize else ''
    cmd = f'mkfs.{filesystem.name} {force_param} {device.system_path} {block_size_param}'
    cmd = re.sub(' +', ' ', cmd)
    TestRun.executor.run_expect_success(cmd)
    TestRun.LOGGER.info(
        f"Successfully created filesystem on device: {device.system_path}")


def create_partition_table(device, partition_table_type: PartitionTable = PartitionTable.gpt):
    TestRun.LOGGER.info(
        f"Creating partition table ({partition_table_type.name}) for device: {device.system_path}")
    cmd = f'parted --script {device.system_path} mklabel {partition_table_type.name}'
    TestRun.executor.run_expect_success(cmd)
    device.partition_table = partition_table_type
    TestRun.LOGGER.info(
        f"Successfully created {partition_table_type.name} "
        f"partition table on device: {device.system_path}")


def get_partition_path(parent_dev, number):
    # TODO: change this to be less specific hw dependent
    id_separator = 'p' if parent_dev[-1].isdigit() else ''
    return f'{parent_dev}{id_separator}{number}'


def create_partition(
        device,
        part_size,
        part_number,
        part_type: PartitionType = PartitionType.primary,
        unit=Unit.MebiByte,
        aligned: bool = True):
    TestRun.LOGGER.info(
        f"Creating {part_type.name} partition on device: {device.system_path}")

    begin = get_first_partition_offset(device, aligned)
    for part in device.partitions:
        begin += part.size
        if part.type == PartitionType.logical:
            begin += Size(1, Unit.MebiByte if not aligned else device.block_size)

    if part_type == PartitionType.logical:
        begin += Size(1, Unit.MebiByte if not aligned else device.block_size)

    end = (begin + part_size) if part_size != Size.zero() else '100%'

    cmd = f'parted --script {device.system_path} mkpart ' \
          f'{part_type.name} ' \
          f'{begin.get_value(unit)}{unit_to_string(unit)} ' \
          f'{end.get_value(unit)}{unit_to_string(unit)}'
    output = TestRun.executor.run(cmd)

    if output.exit_code != 0:
        TestRun.executor.run_expect_success("partprobe")

    TestRun.executor.run_expect_success("udevadm settle")
    if not check_partition_after_create(
            part_size,
            part_number,
            device.system_path,
            part_type,
            aligned):
        raise Exception("Could not create partition!")

    if part_type != PartitionType.extended:
        from storage_devices.partition import Partition
        new_part = Partition(device,
                             part_type,
                             part_number,
                             begin,
                             end if type(end) is Size else device.size)
        dd = Dd().input("/dev/zero") \
                 .output(new_part.system_path) \
                 .count(1) \
                 .block_size(Size(1, Unit.Blocks4096)) \
                 .oflag("direct")
        dd.run()
        device.partitions.append(new_part)

    TestRun.LOGGER.info(f"Successfully created {part_type.name} partition on {device.system_path}")


def create_partitions(device, sizes: [], partition_table_type=PartitionTable.gpt):
    create_partition_table(device, partition_table_type)
    partition_type = PartitionType.primary
    partition_number_offset = 0

    for s in sizes:
        size = Size(
            s.get_value(device.block_size) - device.block_size.value, device.block_size)
        if partition_table_type == PartitionTable.msdos and \
                len(sizes) > 4 and len(device.partitions) == 3:
            create_partition(device,
                             Size.zero(),
                             4,
                             PartitionType.extended)
            partition_type = PartitionType.logical
            partition_number_offset = 1

        partition_number = len(device.partitions) + 1 + partition_number_offset
        create_partition(device,
                         size,
                         partition_number,
                         partition_type,
                         Unit.MebiByte,
                         True)


def get_block_size(device):
    try:
        block_size = float(TestRun.executor.run(
            f"cat {get_sysfs_path(device)}/queue/hw_sector_size").stdout)
    except ValueError:
        block_size = Unit.Blocks512.value
    return block_size


def get_size(device):
    output = TestRun.executor.run_expect_success(f"cat {get_sysfs_path(device)}/size")
    blocks_count = int(output.stdout)
    return blocks_count * int(get_block_size(device))


def get_sysfs_path(device):
    sysfs_path = f"/sys/class/block/{device}"
    if TestRun.executor.run(f"test -d {sysfs_path}").exit_code != 0:
        sysfs_path = f"/sys/block/{device}"
    return sysfs_path


def check_partition_after_create(size, part_number, parent_dev_path, part_type, aligned):
    partition_path = get_partition_path(parent_dev_path, part_number)
    cmd = f"find {partition_path} -type b"
    output = TestRun.executor.run_expect_success(cmd).stdout
    if partition_path not in output:
        TestRun.LOGGER.info(
            "Partition created, but could not find it in system, trying 'hdparm -z'")
        TestRun.executor.run_expect_success(f"hdparm -z {parent_dev_path}")
        output_after_hdparm = TestRun.executor.run_expect_success(
            f"parted --script {parent_dev_path} print").stdout
        TestRun.LOGGER.info(output_after_hdparm)

    counter = 0
    while partition_path not in output and counter < 10:
        time.sleep(2)
        output = TestRun.executor.run(cmd).stdout
        counter += 1

    if len(output.split('\n')) > 1 or partition_path not in output:
        return False

    if aligned and part_type != PartitionType.extended \
            and size.get_value(Unit.Byte) % Unit.Blocks4096.value != 0:
        TestRun.LOGGER.warning(
            f"Partition {partition_path} is not 4k aligned: {size.get_value(Unit.KibiByte)}KiB")

    if part_type == PartitionType.extended or \
            get_size(partition_path.replace('/dev/', '')) == size.get_value(Unit.Byte):
        return True

    TestRun.LOGGER.warning(
        f"Partition size {get_size(partition_path.replace('/dev/', ''))} does not match expected "
        f"{size.get_value(Unit.Byte)} size.")
    return True


def get_first_partition_offset(device, aligned: bool):
    if aligned:
        return Size(1, Unit.MebiByte)
    # 33 sectors are reserved for the backup GPT
    return Size(34, Unit(device.blocksize)) \
        if device.partition_table == PartitionTable.gpt else Size(1, device.blocksize)


def remove_partitions(device):
    if device.is_mounted():
        device.unmount()

    for partition in device.partitions:
        unmount(partition)

    TestRun.LOGGER.info(f"Removing partitions from device: {device.system_path}.")
    dd = Dd().input("/dev/zero") \
        .output(device.system_path) \
        .count(1) \
        .block_size(Size(1, Unit.Blocks4096))\
        .oflag("direct")
    dd.run()
    output = TestRun.executor.run(f"ls {device.system_path}* -1")
    if len(output.stdout.split('\n')) > 1:
        TestRun.LOGGER.error(f"Could not remove partitions from device {device.system_path}")
        return False
    return True


def mount(device, mount_point, options: [str] = None):
    if not fs_utils.check_if_directory_exists(mount_point):
        fs_utils.create_directory(mount_point, True)
    TestRun.LOGGER.info(f"Mounting device {device.system_path} to {mount_point}.")
    cmd = f"mount {device.system_path} {mount_point}"
    if options:
        cmd = f"{cmd} -o {','.join(options)}"
    output = TestRun.executor.run(cmd)
    if output.exit_code != 0:
        raise Exception(f"Failed to mount {device.system_path} to {mount_point}")
    device.mount_point = mount_point


def unmount(device):
    TestRun.LOGGER.info(f"Unmounting device {device.system_path}.")
    if device.mount_point is not None:
        output = TestRun.executor.run(f"umount {device.mount_point}")
        if output.exit_code != 0:
            TestRun.LOGGER.error("Could not unmount device.")
            return False
        return True
    else:
        TestRun.LOGGER.info("Device is not mounted.")
        return True


def unit_to_string(unit):
    unit_string = {
        Unit.Byte: 'B',
        Unit.Blocks512: 's',
        Unit.Blocks4096: 's',
        Unit.KibiByte: 'KiB',
        Unit.MebiByte: 'MiB',
        Unit.GibiByte: 'GiB',
        Unit.TebiByte: 'TiB',
        Unit.KiloByte: 'kB',
        Unit.MegaByte: 'MB',
        Unit.GigaByte: 'GB',
        Unit.TeraByte: 'TB'
    }
    return unit_string.get(unit, "Invalid unit.")


def wipe_filesystem(device, force=True):
    TestRun.LOGGER.info(
        f"Deleting filesystem ({device.filesystem.name}) on device: {device.system_path}")
    force_param = ' -f' if force else ''
    cmd = f'wipefs -a{force_param} {device.system_path}'
    TestRun.executor.run_expect_success(cmd)
    TestRun.LOGGER.info(
        f"Successfully wiped filesystem from device: {device.system_path}")


def get_device_filesystem_type(device_system_path):
    cmd = f'lsblk -l -o NAME,FSTYPE | grep "{device_system_path.replace("/dev/", "")} "'
    stdout = TestRun.executor.run_expect_success(cmd).stdout
    split_stdout = stdout.strip().split()
    if len(split_stdout) <= 1:
        return None
    else:
        try:
            return Filesystem[split_stdout[1]]
        except KeyError:
            TestRun.LOGGER.warning(f"Unrecognized filesystem: {split_stdout[1]}")
            return None
