#!/usr/bin/env python3


from .monitor import Monitor
from .psutil_monitor import PsUtilMonitor


monitor_map = {
    "psutil": PsUtilMonitor,
}


__all__ = [
    "Monitor",
    "PsUtilMonitor",
    "monitor_map",
]
