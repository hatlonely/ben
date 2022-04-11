#!/usr/bin/env python3


import threading
import time
import psutil
from datetime import datetime, timedelta

from ..util import merge
from .monitor import Monitor


class PsUtilMonitor(Monitor):
    def __init__(self, args=None):
        args = merge(args, {
            "seconds": 0,
            "metrics": [
                "CPU", "Mem"
            ],
            "networkInterface": "eth0"
        })
        self.metrics = []
        self.stop = False
        self.network_interface = args["networkInterface"]

        self.delay = args["seconds"] / 100
        if self.delay == 0:
            self.delay = 1
        elif self.delay <= 0.1:
            self.delay = 0.1

        self.enable_metrics = set(args["metrics"])
        self.thread = None

    def collect(self):
        self.thread = threading.Thread(target=self.collect_thread)
        self.thread.start()

    def stat(self, start, end):
        self.stop = True
        self.thread.join()
        return self.metrics[1:]

    def collect_thread(self):
        now = datetime.now()
        while not self.stop:
            metric = {}
            if "CPU" in self.enable_metrics:
                metric["CPU"] = psutil.cpu_percent()
            if "Mem" in self.enable_metrics:
                metric["Mem"] = psutil.virtual_memory().used
            if "Disk" in self.enable_metrics:
                metric["Disk"] = psutil.disk_usage("/").used
            if "IO" in self.enable_metrics:
                io = psutil.disk_io_counters(perdisk=False)
                metric["IOR"] = io.read_count
                metric["IOW"] = io.write_count
            if "Network" in self.enable_metrics:
                net_io = psutil.net_io_counters(pernic=True)
                if self.network_interface in net_io:
                    net_io = net_io[self.network_interface]
                    metric["NetIOR"] = net_io.bytes_recv
                    metric["NetIOW"] = net_io.bytes_sent
            self.metrics.append(metric)
            time.sleep((now - datetime.now()).total_seconds() + self.delay)
            now += timedelta(seconds=self.delay)
