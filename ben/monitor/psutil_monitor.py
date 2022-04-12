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
            "interval": 1,
            "metrics": [
                "CPU", "Mem"
            ],
            "networkInterface": "eth0"
        })
        self.metrics = []
        self.stop = False
        self.network_interface = args["networkInterface"]

        self.delay = args["interval"]
        self.enable_metrics = set(args["metrics"])
        self.thread = None

        self.mutex = threading.Lock()

    def keys(self):
        k = []
        if "CPU" in self.enable_metrics:
            k.append({"name": "CPU", "unit": "percent"})
        if "Mem" in self.enable_metrics:
            k.append({"name": "Mem", "unit": "byte"})
        if "Disk" in self.enable_metrics:
            k.append({"name": "Disk", "unit": "byte"})
        if "IO" in self.enable_metrics:
            k.append({"name": "IOR", "unit": "times"})
            k.append({"name": "IOW", "unit": "times"})
        if "Network" in self.enable_metrics:
            net_io = psutil.net_io_counters(pernic=True)
            if self.network_interface in net_io:
                k.append({"name": "NetIOR", "unit": "bit"})
                k.append({"name": "NetIOW", "unit": "bit"})
        return k

    def collect(self):
        self.thread = threading.Thread(target=self.collect_thread)
        self.thread.start()

    def stat(self, start, end):
        with self.mutex:
            self.stop = True
        self.thread.join()
        return [self.metrics[1:]]

    def collect_thread(self):
        now = datetime.now()
        while True:
            metric = {
                "time": now.isoformat()
            }
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
            sleep_time = (now - datetime.now()).total_seconds() + self.delay
            if sleep_time > 0:
                time.sleep(sleep_time)
                now += timedelta(seconds=self.delay)
            else:
                now = datetime.now()
            with self.mutex:
                if self.stop:
                    break
