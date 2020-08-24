#
# Copyright(c) 2019-2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#

import fcntl
from time import sleep
from contextlib import contextmanager


class LockError(Exception):
    """Raised when unable to lock a file"""


@contextmanager
def lock_file(fd):
    """
    lock file before accessing it
    if lock failed then file is already locked,
    in such case do 10 attempts with 1 sleep pause to acquire file
    """
    for i in range(20):
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
            # if lock was aquired succesfully - exit the loop, no need to iterate further
            break
        except BlockingIOError:
            sleep(0.5)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    else:
        raise LockError(f"Can't acquire lock on {fd.name} file!")
