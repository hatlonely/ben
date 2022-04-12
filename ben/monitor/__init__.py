#!/usr/bin/env python3


from .monitor import Monitor
from .psutil_monitor import PsUtilMonitor
from .cms_monitor import CMSMonitor


monitor_map = {
    "psutil": PsUtilMonitor,
    "ecs": CMSMonitor,
}


__all__ = [
    "Monitor",
    "PsUtilMonitor",
    "CMSMonitor",
    "monitor_map",
]
