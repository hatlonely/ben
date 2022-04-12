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
        self.stop = False
        self.thread = None
        self.mutex = threading.Lock()

        self.network_interface = args["networkInterface"]
        self.delay = args["interval"]

        self.metrics = dict([(k, []) for k in args["metrics"]])

    def unit(self):
        return {
            "CPU": "percent",
            "Mem": "byte",
            "Disk": "byte",
            "IOR": "times",
            "IOW": "times",
            "NetIOR": "bit",
            "NetIOW": "bit",
        }

    def collect(self):
        self.thread = threading.Thread(target=self.collect_thread)
        self.thread.start()

    def stat(self, start, end):
        with self.mutex:
            self.stop = True
        self.thread.join()
        # 第一次统计不准确，丢弃第一次统计
        return dict([(k, v[1:])for k, v in self.metrics.items()])

    def collect_thread(self):
        now = datetime.now()
        while True:
            if "CPU" in self.metrics:
                self.metrics["CPU"].append({
                    "time": now.isoformat(),
                    "value": psutil.cpu_percent(),
                })
            if "Mem" in self.metrics:
                self.metrics["Mem"].append({
                    "time": now.isoformat(),
                    "value": psutil.virtual_memory().used,
                })
            if "Disk" in self.metrics:
                self.metrics["Disk"].append({
                    "time": now.isoformat(),
                    "value": psutil.disk_usage("/").used,
                })
            if "IOR" in self.metrics or "IOW" in self.metrics:
                io = psutil.disk_io_counters(perdisk=False)
                if "IOR" in self.metrics:
                    self.metrics["IOR"].append({
                        "time": now.isoformat(),
                        "value": io.read_count,
                    })
                if "IOW" in self.metrics:
                    self.metrics["IOW"].append({
                        "time": now.isoformat(),
                        "value": io.write_count,
                    })
            if "NetIOR" in self.metrics or "NetIOW" in self.metrics:
                net_io = psutil.net_io_counters(pernic=True)
                if self.network_interface in net_io:
                    net_io = net_io[self.network_interface]
                    if "NetIOR" in self.metrics:
                        self.metrics["NetIOR"].append({
                            "time": now.isoformat(),
                            "value": net_io.bytes_recv,
                        })
                    if "NetIOW" in self.metrics:
                        self.metrics["NetIOW"].append({
                            "time": now.isoformat(),
                            "value": net_io.bytes_sent,
                        })

            sleep_time = (now - datetime.now()).total_seconds() + self.delay
            if sleep_time > 0:
                time.sleep(sleep_time)
                now += timedelta(seconds=self.delay)
            else:
                now = datetime.now()
            with self.mutex:
                if self.stop:
                    break
