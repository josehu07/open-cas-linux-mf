#
# Copyright(c) 2019-2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#

from test_tools import fs_utils
from test_utils import systemd


def add_mountpoint(device, mount_point, fs_type):
    fs_utils.append_line("/etc/fstab",
                         f"{device.system_path} {mount_point} {fs_type.name} defaults 0 0")
    systemd.reload_daemon()
    systemd.restart_service("local-fs.target")


def remove_mountpoint(device):
    fs_utils.remove_lines("/etc/fstab", device.system_path)
    systemd.reload_daemon()
