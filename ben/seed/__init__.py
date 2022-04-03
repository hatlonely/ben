#!/usr/bin/env python3


from .seed import Seed
from .dict_seed import DictSeed
from .file_seed import FileSeed


seed_map = {
    "dict": DictSeed,
    "file": FileSeed,
}


__all__ = [
    "Seed",
    "DictSeed",
    "FileSeed",
    "seed_map",
]
