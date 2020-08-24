#
# Copyright(c) 2019-2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#

from core.test_run import TestRun


def reload_daemon():
    TestRun.executor.run_expect_success("systemctl daemon-reload")


def restart_service(name):
    TestRun.executor.run_expect_success(f"systemctl restart {name}")
