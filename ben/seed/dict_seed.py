#!/usr/bin/env python3
import random

from .seed import Seed


class DictSeed(Seed):
    def __init__(self, args):
        self.seeds = args

    def pick(self):
        return random.choice(self.seeds)
