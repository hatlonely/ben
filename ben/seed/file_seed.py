#!/usr/bin/env python3
import json
import random

from .seed import Seed
from ..util import merge, REQUIRED


class FileSeed(Seed):
    def __init__(self, args):
        args = merge(args, {
            "name": REQUIRED
        })
        self.seeds = []
        with open(args["name"]) as fp:
            for line in fp:
                self.seeds.append(json.loads(line))

    def pick(self):
        return random.choice(self.seeds)
