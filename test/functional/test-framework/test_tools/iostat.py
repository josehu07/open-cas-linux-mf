#
# Copyright(c) 2020 Intel Corporation
# SPDX-License-Identifier: BSD-3-Clause-Clear
#

from core.test_run import TestRun
from storage_devices.device import Device
from test_utils.size import Size, Unit, UnitPerSecond
from test_utils.time import Time


class IOstatExtended:
    iostat_option = "x"

    def __init__(self, device_name: str, raw_stats: list = None):
        metrics_number = 13
        if raw_stats is None:
            raw_stats = [0] * metrics_number
        if len(raw_stats) < metrics_number:
            raw_stats.extend([0] * metrics_number)

        self.device_name = device_name
        # rrqm/s
        self.read_requests_merged_per_sec = float(raw_stats[0])
        # wrqm/s
        self.write_requests_merged_per_sec = float(raw_stats[1])
        # r/s
        self.read_requests_per_sec = float(raw_stats[2])
        # w/s
        self.write_requests_per_sec = float(raw_stats[3])
        # rkB/s
        self.reads_per_sec = Size(float(raw_stats[4]), UnitPerSecond(Unit.KiloByte))
        # wkB/s
        self.writes_per_sec = Size(float(raw_stats[5]), UnitPerSecond(Unit.KiloByte))
        # avgrq-sz
        self.average_request_size = float(raw_stats[6])  # `in sectors`
        # avgqu-sz
        self.average_queue_length = float(raw_stats[7])
        # await
        self.average_service_time = Time(milliseconds=float(raw_stats[8]))
        # r_await
        self.read_average_service_time = Time(milliseconds=float(raw_stats[9]))
        # w_await
        self.write_average_service_time = Time(milliseconds=float(raw_stats[10]))
        # iostat's documentation says to not trust 11th field
        # util
        self.utilization = float(raw_stats[12])

    def __str__(self):
        return (
            f"\n=========={self.device_name} IO stats: ==========\n"
            f"Read requests merged per second: {self.read_requests_merged_per_sec}\n"
            f"Write requests merged per second: {self.write_requests_merged_per_sec}\n"
            f"Read requests: {self.read_requests_per_sec}\n"
            f"Write requests: {self.write_requests_per_sec}\n"
            f"Reads per second: {self.reads_per_sec}\n"
            f"Writes per second {self.writes_per_sec}\n"
            f"Average request size: {self.average_request_size} blocks\n"
            f"Average queue length {self.average_queue_length}\n"
            f"Average service time: {self.average_service_time}\n"
            f"Read average service time {self.read_average_service_time}\n"
            f"Write average service time: {self.write_average_service_time}\n"
            f"Utilization: {self.utilization}\n"
            f"=================================================\n"
        )

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not other:
            return False
        return (
            self.read_requests_merged_per_sec == other.read_requests_merged_per_sec
            and self.write_requests_merged_per_sec
            == other.write_requests_merged_per_sec
            and self.read_requests_per_sec == other.read_requests_per_sec
            and self.write_requests_per_sec == other.write_requests_per_sec
            and self.reads_per_sec == other.reads_per_sec
            and self.writes_per_sec == other.writes_per_sec
            and self.average_request_size == other.average_request_size
            and self.average_queue_length == other.average_queue_length
            and self.average_service_time == other.average_service_time
            and self.read_average_service_time == other.read_average_service_time
            and self.write_average_service_time == other.write_average_service_time
            and self.utilization == other.utilization
        )

    @classmethod
    def get_iostat_list(
            cls,
            devices_list: [Device],
            since_boot: bool = True,
            interval: int = 1,
    ):
        """
            Returns list of IOstat objects containing extended statistics displayed
            in kibibytes/kibibytes per second.
        """
        return _get_iostat_list(cls, devices_list, since_boot, interval)


class IOstatBasic:
    iostat_option = "d"

    def __init__(self, device_name: str, raw_stats: list = None):
        metrics_number = 5
        if raw_stats is None:
            raw_stats = [0] * metrics_number
        if len(raw_stats) < metrics_number:
            raw_stats.extend([0] * metrics_number)

        self.device_name = device_name
        # tps
        self.transfers_per_second = float(raw_stats[0])
        # kB_read/s
        self.reads_per_second = Size(float(raw_stats[1]), UnitPerSecond(Unit.KiloByte))
        # kB_wrtn/s
        self.writes_per_second = Size(float(raw_stats[2]), UnitPerSecond(Unit.KiloByte))
        # kB_read
        self.total_reads = Size(float(raw_stats[3]), Unit.KibiByte)
        # kB_wrtn
        self.total_writes = Size(float(raw_stats[4]), Unit.KibiByte)

    def __str__(self):
        return (
            f"\n=========={self.device_name} IO stats: ==========\n"
            f"Transfers per second: {self.transfers_per_second}\n"
            f"Kilobytes read per second: {self.reads_per_second}\n"
            f"Kilobytes written per second: {self.writes_per_second}\n"
            f"Kilobytes read: {self.total_reads}\n"
            f"Kilobytes written: {self.total_writes}\n"
            f"=================================================\n"
        )

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if not isinstance(other, IOstatBasic):
            return False
        return vars(self) == vars(other)

    @classmethod
    def get_iostat_list(
            cls,
            devices_list: [Device],
            since_boot: bool = True,
            interval: int = 1,
    ):
        """
            Returns list of IOstat objects containing basic statistics displayed
            in kibibytes/kibibytes per second.
        """
        return _get_iostat_list(cls, devices_list, since_boot, interval)


def _get_iostat_list(
        class_type: type,
        devices_list: [Device],
        since_boot: bool,
        interval: int,
):
    if interval < 1:
        raise ValueError("iostat interval must be positive!")

    iostat_cmd = f"iostat -k -{class_type.iostat_option} "

    if not since_boot:
        iostat_cmd += f"-y {interval} 1 "

    iostat_cmd += " ".join(
        [name.system_path.strip("/dev/") for name in devices_list]
    )
    grep_pattern = "\\|".join(
        [name.system_path.strip("/dev/") for name in devices_list]
    )

    lines = TestRun.executor.run(
        f"{iostat_cmd} " f'| grep "{grep_pattern}"'
    ).stdout.splitlines()

    ret = []
    for line in lines:
        args = line.split()

        dev_name = args[0]
        raw_stats = args[1:]
        ret += [class_type(device_name=dev_name, raw_stats=raw_stats)]

    return ret
