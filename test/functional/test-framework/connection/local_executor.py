#
# Copyright(c) 2019-2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#

import subprocess
from datetime import timedelta

from connection.base_executor import BaseExecutor
from test_utils.output import Output


class LocalExecutor(BaseExecutor):
    def _execute(self, command, timeout):
        completed_process = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout.total_seconds())

        return Output(completed_process.stdout,
                      completed_process.stderr,
                      completed_process.returncode)

    def _rsync(self, src, dst, delete=False, symlinks=False, checksum=False, exclude_list=[],
               timeout: timedelta = timedelta(seconds=30), dut_to_controller=False):
        options = []

        if delete:
            options.append("--delete")
        if symlinks:
            options.append("--links")
        if checksum:
            options.append("--checksum")

        for exclude in exclude_list:
            options.append(f"--exclude {exclude}")

        subprocess.run(
            f'rsync -r {src} {dst} {" ".join(options)}',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout.total_seconds())
