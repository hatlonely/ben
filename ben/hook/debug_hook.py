#!/usr/bin/env python3


import json

from .hook import Hook
from ..result import TestResult, PlanResult, UnitResult, StepResult
from ..util import merge


class DebugHook(Hook):
    def __init__(self, args, test_id=""):
        super().__init__(args, test_id)
        args = merge(args, {
            "padding": "  "
        })
        self.padding_to_add = args["padding"]
        self.padding = ""

    def on_test_start(self, test_info):
        print("{}{i18n.title.test} {name}".format(self.padding, name=test_info["name"], i18n=self.i18n))
        self.padding += self.padding_to_add

    def on_test_end(self, res: TestResult):
        self.padding = self.padding[:-len(self.padding_to_add)]
        print("{}{i18n.title.test} {name}".format(self.padding, name=res.name, i18n=self.i18n))

    def on_plan_start(self, plan_info):
        print("{}{i18n.title.plan} {name}".format(self.padding, name=plan_info["name"], i18n=self.i18n))
        self.padding += self.padding_to_add
        DebugHook.debug_object(self.padding, "PlanInfo", plan_info)

    def on_plan_end(self, res: PlanResult):
        self.padding = self.padding[:-len(self.padding_to_add)]
        print("{}{i18n.title.plan} {name}".format(self.padding, name=res.name, i18n=self.i18n))
        DebugHook.debug_object(self.padding, "PlanResult", res)

    def on_unit_start(self, unit_info):
        print("{}{i18n.title.unit} {name}".format(self.padding, name=unit_info["name"], i18n=self.i18n))
        self.padding += self.padding_to_add
        DebugHook.debug_object(self.padding, "UnitInfo", unit_info)

    def on_unit_end(self, res: UnitResult):
        self.padding = self.padding[:-len(self.padding_to_add)]
        print("{}{i18n.title.unit} {name}".format(self.padding, name=res.name, i18n=self.i18n))
        DebugHook.debug_object(self.padding, "UnitResult", res)

    def on_step_start(self, step_info):
        print("{}{i18n.title.step}".format(self.padding, i18n=self.i18n))
        self.padding += self.padding_to_add
        DebugHook.debug_object(self.padding, "StepInfo", step_info)

    def on_step_end(self, res: StepResult):
        self.padding = self.padding[:-len(self.padding_to_add)]
        print("{}{i18n.title.step}".format(self.padding, i18n=self.i18n))
        DebugHook.debug_object(self.padding, "StepResult", res)

    @staticmethod
    def debug_object(padding, title, result):
        print("\n".join([padding + line for line in ("{}: {}".format(title, json.dumps(result, indent=2))).split("\n")]))
