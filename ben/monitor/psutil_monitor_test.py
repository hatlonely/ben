#!/usr/bin/env python3


import time
import unittest
from datetime import datetime

from .psutil_monitor import PsUtilMonitor


class TestPsUtilMonitor(unittest.TestCase):
    def test_psutil_monitor(self):
        m = PsUtilMonitor({
            "metrics": [
                "CPU", "Mem", "Disk", "IO", "Network",
            ],
            "networkInterface": "en3",
        })

        m.collect()

        time.sleep(3)

        stat = m.stat(datetime.now(), datetime.now())
        print(stat)
