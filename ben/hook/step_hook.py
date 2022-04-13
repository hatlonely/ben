#!/usr/bin/env python3


import json

from .hook import Hook
from ..result import StepResult


class StepHook(Hook):
    def __init__(self, args, test_id=""):
        super().__init__(args, test_id)

    def on_step_end(self, res: StepResult):
        print(json.dumps(res.to_json()))
