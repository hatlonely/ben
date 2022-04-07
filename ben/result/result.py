#!/usr/bin/env python3


from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SubStepResult:
    req: any
    res: any
    name: str
    code: str
    success: bool
    elapse: timedelta

    def to_json(self):
        return {
            "req": self.req,
            "res": self.res,
            "name": self.name,
            "code": self.code,
            "success": self.success,
            "elapse": int(self.elapse.total_seconds() * 1000000),
        }

    @staticmethod
    def from_json(obj):
        res = SubStepResult(
            req=obj["req"],
            res=obj["res"],
            name=obj["name"],
            code=obj["code"],
            success=obj["success"],
            elapse=timedelta(microseconds=obj["elapse"])
        )
        return res


@dataclass
class StepResult:
    step: list[SubStepResult]
    code: str
    success: bool
    elapse: timedelta

    def to_json(self):
        return {
            "step": self.step,
            "code": self.code,
            "success": self.success,
            "elapse": int(self.elapse.total_seconds() * 1000000),
        }

    @staticmethod
    def from_json(obj):
        res = StepResult()
        res.step = obj["step"]
        res.code = obj["code"]
        res.success = obj["success"]
        res.elapse = timedelta(microseconds=obj["elapse"])
        return res

    def __init__(self):
        self.step = []
        self.code = ""
        self.success = True
        self.elapse = timedelta(seconds=0)

    def add_sub_step_result(self, result: SubStepResult):
        self.step.append(result)
        self.elapse += result.elapse
        if not result.success:
            self.success = False
            self.code = "{}.{}".format(result.name, result.code)


@dataclass
class UnitResult:
    name: str
    success: int
    total: int
    qps: float
    code: dict
    elapse: timedelta
    rate: float
    avgResTime: timedelta
    start_time: datetime
    end_time: datetime
    total_elapse: timedelta

    def to_json(self):
        return {
            "success": self.success,
            "total": self.total,
            "qps": self.qps,
            "code": self.code,
            "elapse": int(self.elapse.total_seconds() * 1000000),
            "rate": self.rate,
            "avgResTime": self.avgResTime,
        }

    @staticmethod
    def from_json(obj):
        res = UnitResult(name=obj["name"])
        res.success = obj["success"]
        res.total = obj["total"]
        res.qps = obj["qps"]
        res.code = obj["code"]
        res.elapse = timedelta(microseconds=obj["elapse"])
        res.rate = obj["rate"]
        res.avgResTime = timedelta(microseconds=obj["avgResTime"])
        return res

    def __init__(self, name):
        self.name = name
        self.success = 0
        self.total = 0
        self.qps = 0
        self.code = {}
        self.elapse = timedelta(seconds=0)
        self.rate = 0
        self.avgResTime = timedelta(seconds=0)
        self.start_time = datetime.now()

    def add_step_result(self, result: StepResult):
        self.total += 1
        if result.success:
            self.success += 1
            self.elapse += result.elapse
        else:
            if result.code not in self.code:
                self.code[result.code] = 0
            self.code[result.code] += 1

    def stop(self):
        self.end_time = datetime.now()
        self.total_elapse = self.end_time - self.start_time

    def summary(self):
        self.qps = self.success / self.total_elapse.total_seconds()
        self.avgResTime = self.elapse / self.qps
        self.rate = self.success / self.total


@dataclass
class PlanResult:
    id_: str
    is_err: bool
    err: str
    units: list[UnitResult]

    def to_json(self):
        return {
            "id": self.id_,
            "isErr": self.is_err,
            "err": self.err,
            "units": self.units
        }

    @staticmethod
    def from_json(obj):
        res = PlanResult(obj["id"])
        res.is_err = obj["isErr"]
        res.err = obj["err"]
        res.units = [UnitResult.from_json(i) for i in obj["units"]]

    def __init__(self, id_):
        self.id_ = id_
        self.is_err = False
        self.err = ""
        self.units = []

    def add_unit_result(self, unit):
        self.units.append(unit)


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
        self.is_err = False
        self.err = ""
        self.plans = []
        self.sub_tests = []
        if err_message:
            self.is_err = True
            self.err = err_message

    def add_plan_result(self, plan):
        self.plans.append(plan)

    def add_sub_test_result(self, sub_test):
        self.sub_tests.append(sub_test)
