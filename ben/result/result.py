#!/usr/bin/env python3


from dataclasses import dataclass
from datetime import datetime, timedelta
from dateutil import parser


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
    is_err: bool
    err: str

    def to_json(self):
        return {
            "step": self.step,
            "code": self.code,
            "success": self.success,
            "elapse": int(self.elapse.total_seconds() * 1000000),
            "isErr": self.is_err,
            "err": self.err,
        }

    @staticmethod
    def from_json(obj):
        res = StepResult()
        res.step = obj["step"]
        res.code = obj["code"]
        res.success = obj["success"]
        res.elapse = timedelta(microseconds=obj["elapse"])
        res.is_err = obj["isErr"]
        res.err = obj["err"]
        return res

    def __init__(self, err_message=None):
        self.step = []
        self.code = ""
        self.success = True
        self.elapse = timedelta(seconds=0)
        self.is_err = False
        self.err = ""
        if err_message:
            self.is_err = True
            self.err = err_message

    def add_sub_step_result(self, result: SubStepResult):
        self.step.append(result)
        self.elapse += result.elapse
        if not result.success:
            self.success = False
            self.code = "{}.{}".format(result.name, result.code)

    def add_err_result(self, name, err):
        self.is_err = True
        self.err = err
        self.success = False
        self.code = "{}.{}".format(name, "ERROR")


@dataclass
class UnitResult:
    name: str
    parallel: int
    limit: int
    success: int
    total: int
    qps: float
    code: dict
    elapse: timedelta
    rate: float
    res_time: timedelta
    start_time: datetime
    end_time: datetime
    total_elapse: timedelta
    is_err: bool
    err: str

    def to_json(self):
        return {
            "name": self.name,
            "parallel": self.parallel,
            "limit": self.limit,
            "success": self.success,
            "total": self.total,
            "qps": self.qps,
            "code": self.code,
            "elapse": int(self.elapse.total_seconds() * 1000000),
            "rate": self.rate,
            "resTime": int(self.res_time.total_seconds() * 1000000),
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat(),
            "isErr": self.is_err,
            "err": self.err,
        }

    @staticmethod
    def from_json(obj):
        res = UnitResult(obj["name"], obj["parallel"], obj["limit"])
        res.success = obj["success"]
        res.total = obj["total"]
        res.qps = obj["qps"]
        res.code = obj["code"]
        res.elapse = timedelta(microseconds=obj["elapse"])
        res.rate = obj["rate"]
        res.res_time = timedelta(microseconds=obj["resTime"])
        res.start_time = parser.parse(obj["startTime"])
        res.end_time = parser.parse(obj["endTime"])
        res.is_err = obj["isErr"]
        res.err = obj["err"]
        return res

    def __init__(self, name, parallel, limit, err_message=None):
        self.name = name
        self.parallel = parallel
        self.limit = limit
        self.success = 0
        self.total = 0
        self.qps = 0
        self.code = {}
        self.elapse = timedelta(seconds=0)
        self.rate = 0
        self.res_time = timedelta(seconds=0)
        self.start_time = datetime.now()
        self.end_time = datetime.now()
        self.total_elapse = timedelta(seconds=0)
        self.is_err = False
        self.err = ""
        if err_message:
            self.is_err = True
            self.err = err_message

    def add_step_result(self, result: StepResult):
        self.total += 1
        if result.success:
            self.success += 1
            self.elapse += result.elapse
        else:
            if result.code not in self.code:
                self.code[result.code] = 0
            self.code[result.code] += 1

    def summary(self):
        self.end_time = datetime.now()
        self.total_elapse = self.end_time - self.start_time
        self.qps = self.success / self.total_elapse.total_seconds()
        self.res_time = self.elapse / self.qps
        self.rate = self.success / self.total


@dataclass
class UnitGroup:
    idx = 0
    seconds = 0
    times = 0
    units = list[UnitResult]()

    def to_json(self):
        return {
            "idx": self.idx,
            "seconds": self.seconds,
            "times": self.times,
            "units": self.units,
        }

    @staticmethod
    def from_json(obj):
        res = UnitGroup()
        res.idx = obj["idx"]
        res.seconds = obj["seconds"]
        res.times = obj["times"]
        res.units = [UnitResult.from_json(i) for i in obj["units"]]
        return res

    def add_unit_result(self, unit):
        self.units.append(unit)


@dataclass
class PlanResult:
    id_: str
    name: str
    is_err: bool
    err: str
    unit_groups: list[UnitGroup]

    def to_json(self):
        return {
            "id": self.id_,
            "name": self.name,
            "isErr": self.is_err,
            "err": self.err,
            "unitGroups": self.unit_groups
        }

    @staticmethod
    def from_json(obj):
        res = PlanResult(obj["id"], obj["name"])
        res.is_err = obj["isErr"]
        res.err = obj["err"]
        res.unit_groups = [UnitGroup.from_json(i) for i in obj["unitGroups"]]

    def __init__(self, id_, name, err_message=None):
        self.id_ = id_
        self.name = name
        self.unit_groups = []
        self.is_err = False
        self.err = ""
        if err_message:
            self.is_err = True
            self.err = err_message

    def add_unit_group(self, unit_group):
        self.unit_groups.append(unit_group)


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
