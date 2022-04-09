#!/usr/bin/env python3


from ..result import TestResult, PlanResult, UnitResult, StepResult
from ..i18n import I18n


class Hook:
    def __init__(self, args=None, test_id=""):
        self.i18n = I18n(args).i18n()
        self.test_id = test_id

    def on_exit(self, res: TestResult):
        pass

    def on_test_start(self, test_info):
        pass

    def on_test_end(self, res: TestResult):
        pass

    def on_plan_start(self, plan_info):
        pass

    def on_plan_end(self, res: PlanResult):
        pass

    def on_unit_start(self, unit_info):
        pass

    def on_unit_end(self, res: UnitResult):
        pass

    def on_step_start(self, step_info):
        pass

    def on_step_end(self, res: StepResult):
        pass
