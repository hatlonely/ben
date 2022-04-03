#!/usr/bin/env python3


from dataclasses import dataclass


@dataclass
class RuntimeConstant:
    pass


@dataclass
class RuntimeContext:
    pass


class Framework:
    def __init__(
        self,
        test_directory=None,
        plan_directory=None,
    ):
        pass

    def format(self):
        pass

    def run(self):
        pass

    def run_plan(self):
        pass
