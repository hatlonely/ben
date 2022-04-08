#!/usr/bin/env python3


import atomics
from datetime import datetime
from ..util import merge


class Stop(object):
    def __init__(self, args):
        args = merge(args, {
            "seconds": 3,
            "times": 0,
        })

        self.now = datetime.now()
        self.seconds = args["seconds"]
        self.times = args["times"]
        self.count = atomics.atomic(width=8, atype=atomics.INT)

    def next(self):
        while True:
            if self.seconds != 0 and (datetime.now() - self.now).total_seconds() > self.seconds:
                return False
            # 有性能瓶颈，mac 上测试，一秒仅能执行 6w 次，且多个 atomic 变量看起来会串行执行
            val = self.count.fetch_inc()
            if self.times != 0 and val >= self.times:
                return False
            yield val
