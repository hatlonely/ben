#!/usr/bin/env python3


from .hook import Hook
from .debug_hook import DebugHook


hook_map = {
    "debug": DebugHook,
}


__all__ = [
    "Hook",
    "DebugHook",
    "hook_map",
]
