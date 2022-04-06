#!/usr/bin/env python3


from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SubStepResult:
    pass


@dataclass
class StepResult:
    pass


@dataclass
class UnitResult:
    pass


@dataclass
class PlanResult:
    id_: str
    success: str
    qps: str
    avgResTime: timedelta
    rate: float
    code: dict
    is_err: bool
    err: str

    def to_json(self):
        return {
            "id": self.id_,
            "success": self.success,
            "qps": self.qps,
            "avgResTime": self.avgResTime,
            "rate": self.rate,
            "code": self.code,
            "isErr": self.is_err,
            "err": self.err,
        }

    @staticmethod
    def from_json(obj):
        res = PlanResult(obj["id"])
        res.success = obj["success"]
        res.qps = obj["qps"]
        res.avgResTime = obj["avgResTime"]
        res.rate = obj["rate"]
        res.code = obj["code"]
        res.is_err = obj["isErr"]
        res.err = obj["err"]

    def __init__(self, id_):
        self.id_ = id_


@dataclass
class TestResult:
    id_: str
    directory: str
    name: str
    description: str
    is_err: bool
    err: str
    plans: list[PlanResult]
    sub_tests: list

    def to_json(self):
        return {
            "id": self.id_,
            "directory": self.directory,
            "name": self.name,
            "description": self.description,
            "isErr": self.is_err,
            "err": self.err,
            "plans": self.plans,
        }

    @staticmethod
    def from_json(obj):
        res = TestResult(
            id_=obj["id"],
            directory=obj["directory"],
            name=obj["name"],
            description=obj["description"],
            err_message=obj["err"],
        )
        res.plans = [PlanResult.from_json(i) for i in obj["plans"]]
        return res

    def __init__(self, id_, directory, name, description="", err_message=None):
        self.id_ = id_
        self.directory = directory
        self.name = name
        self.description = description
        if err_message:
            self.is_err = True
            self.err = err_message

    def add_plan_result(self, plan):
        self.plans.append(plan)

    def add_sub_test_result(self, sub_test):
        self.sub_tests.append(sub_test)
