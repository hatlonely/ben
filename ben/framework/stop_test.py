#!/usr/bin/env python3


import concurrent.futures
import threading
import unittest
from itertools import repeat

from .stop import Stop


def proc(stop):
    cnt = 0
    while stop.next():
        cnt += 1
    return threading.get_ident(), cnt


class TestStop(unittest.TestCase):
    def test_stop(self):
        stop1 = Stop({
            "seconds": 2,
            "times": 0,
        })
        stop2 = Stop({
            "seconds": 2,
            "times": 0,
        })

        pool1 = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        pool2 = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        results1 = pool1.map(proc, repeat(stop1, times=10))
        results2 = pool2.map(proc, repeat(stop2, times=10))

        res = {}
        total = 0
        for tid, cnt in results1:
            res[tid] = cnt
            total += cnt
        print("total:", total)
        print(res)

        res = {}
        total = 0
        for tid, cnt in results2:
            res[tid] = cnt
            total += cnt
        print("total:", total)
        print(res)
