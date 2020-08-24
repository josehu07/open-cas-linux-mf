#
# Copyright(c) 2019-2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#

from storage_devices.device import Device
from test_tools import disk_utils
from test_utils.size import Size


class Partition(Device):
    def __init__(self, parent_dev, type, number, begin: Size, end: Size):
        Device.__init__(self, disk_utils.get_partition_path(parent_dev.system_path, number))
        self.number = number
        self.parent_device = parent_dev
        self.type = type
        self.begin = begin
        self.end = end

    def __str__(self):
        return f"\tsystem path: {self.system_path}, size: {self.size}, type: {self.type}, " \
            f"parent device: {self.parent_device.system_path}\n"
