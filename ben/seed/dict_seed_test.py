#!/usr/bin/env pyhton3


import concurrent.futures
import unittest

from .dict_seed import DictSeed


class TestDictSeed(unittest.TestCase):
    def test_dict_seed(self):
        s = DictSeed(args=[{
            "key1": "val1",
            "key2": "val2",
        }, {
            "key1": "val3",
            "key2": "val4",
        }])

        pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

        for _ in range(100):
            pool.submit(print, s.pick())

