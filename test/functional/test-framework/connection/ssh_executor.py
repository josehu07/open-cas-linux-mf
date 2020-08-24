#
# Copyright(c) 2019-2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#

import socket
import subprocess
from datetime import timedelta, datetime

import paramiko
from paramiko.ssh_exception import NoValidConnectionsError

from connection.base_executor import BaseExecutor
from core.test_run import TestRun
from test_utils.output import Output


class SshExecutor(BaseExecutor):
    def __init__(self, ip, username, password, port=22):
        self.ip = ip
        self.user = username
        self.password = password
        self.port = port
        self.ssh = paramiko.SSHClient()
        self._check_config_for_reboot_timeout()

    def __del__(self):
        self.ssh.close()

    def connect(self, user=None, passwd=None, port=None,
                timeout: timedelta = timedelta(seconds=30)):
        user = user or self.user
        passwd = passwd or self.password
        port = port or self.port
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self.ip, username=user, password=passwd,
                             port=port, timeout=timeout.total_seconds())
        except (paramiko.SSHException, socket.timeout) as e:
            raise ConnectionError(f"An exception of type '{type(e)}' occurred while trying to "
                                  f"connect to {self.ip}\n{e}")

    def disconnect(self):
        try:
            self.ssh.close()
        except Exception:
            raise Exception(f"An exception occurred while trying to disconnect from {self.ip}")

    def _execute(self, command, timeout):
        try:
            (stdin, stdout, stderr) = self.ssh.exec_command(command,
                                                            timeout=timeout.total_seconds())
        except paramiko.SSHException as e:
            raise ConnectionError(f"An exception occurred while executing command '{command}' on"
                                  f" {self.ip}\n{e}")

        return Output(stdout.read(), stderr.read(), stdout.channel.recv_exit_status())

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

        src_to_dst = f"{self.user}@{self.ip}:{src} {dst} " if dut_to_controller else\
                     f"{src} {self.user}@{self.ip}:{dst} "

        completed_process = subprocess.run(
            f'sshpass -p "{self.password}" rsync -r -e "ssh -p {self.port} '
            f'-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no" '
            + src_to_dst + f'{" ".join(options)}',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout.total_seconds())

        if completed_process.returncode:
            raise Exception(f"rsync failed:\n{completed_process}")

    def is_remote(self):
        return True

    def _check_config_for_reboot_timeout(self):
        if "reboot_timeout" in TestRun.config.keys():
            self._parse_timeout_to_int()
        else:
            self.reboot_timeout = None

    def _parse_timeout_to_int(self):
        self.reboot_timeout = int(TestRun.config["reboot_timeout"])
        if self.reboot_timeout < 0:
            raise ValueError("Reboot timeout cannot be negative.")

    def reboot(self):
        self.run("reboot")
        self.wait_for_connection_loss()
        self.wait_for_connection(timedelta(seconds=self.reboot_timeout)) \
            if self.reboot_timeout is not None else self.wait_for_connection()

    def is_active(self):
        try:
            self.ssh.exec_command('', timeout=5)
            return True
        except Exception:
            return False

    def wait_for_connection(self, timeout: timedelta = timedelta(minutes=10)):
        start_time = datetime.now()
        with TestRun.group("Waiting for DUT ssh connection"):
            while start_time + timeout > datetime.now():
                try:
                    self.connect()
                    return
                except Exception:
                    continue
            raise ConnectionError("Timeout occurred while tying to establish ssh connection")

    def wait_for_connection_loss(self, timeout: timedelta = timedelta(minutes=1)):
        with TestRun.group("Waiting for DUT ssh connection loss"):
            end_time = datetime.now() + timeout
            while end_time > datetime.now():
                self.disconnect()
                try:
                    self.connect(timeout=timedelta(seconds=5))
                except Exception:
                    return
            raise ConnectionError("Timeout occurred before ssh connection loss")
