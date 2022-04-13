#!/usr/bin/env python3


from .hook import Hook
from .debug_hook import DebugHook
from .step_hook import StepHook


hook_map = {
    "debug": DebugHook,
    "step": StepHook,
}


__all__ = [
    "Hook",
    "DebugHook",
    "hook_map",
]
