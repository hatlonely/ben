#!/usr/bin/env python3


from .reporter import Reporter


reporter_map = {
    "json": None,
    "html": None,
}


__all__ = [
    "Reporter",
    "reporter_map",
]
