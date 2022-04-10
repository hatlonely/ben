#!/usr/bin/env python3
import random
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
class UnitStageResult:
    time: datetime
    success: int
    total: int
    qps: float
    rate: float
    res_time: timedelta
    elapse: timedelta

    def to_json(self):
        return {
            "time": self.time.isoformat(),
            "success": self.success,
            "total": self.total,
            "qps": self.qps,
            "rate": self.rate,
            "resTime": (self.res_time.total_seconds() * 1000000),
            "elapse": (self.elapse.total_seconds() * 1000000),
        }

    @staticmethod
    def from_json(obj):
        res = UnitStageResult()
        res.time = parser.parse(obj["time"])
        res.success = obj["success"]
        res.total = obj["total"]
        res.qps = obj["qps"]
        res.rate = obj["rate"]
        res.res_time = timedelta(microseconds=obj["resTime"])
        res.elapse = timedelta(microseconds=obj["elapse"])
        return res

    def __init__(self):
        self.time = datetime.now()
        self.success = 0
        self.total = 0
        self.qps = 0
        self.rate = 0
        self.res_time = timedelta(seconds=0)
        self.elapse = timedelta(seconds=0)

    def add_step_result(self, result: StepResult):
        self.total += 1
        if result.success:
            self.success += 1
            self.elapse += result.elapse

    def summary(self):
        total_elapse = datetime.now() - self.time
        self.qps = self.success / total_elapse.total_seconds()
        if self.success != 0:
            self.res_time = self.elapse / self.success
        if self.total != 0:
            self.rate = self.success / self.total


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
    stages: list[UnitStageResult]
    stage_milliseconds: int
    stage_times: int
    current_stage: UnitStageResult
    max_step_size: int
    steps: list[StepResult]
    quantile_keys: list
    quantile: dict

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
            "stages": self.stages,
            "stageMilliseconds": self.stage_milliseconds,
            "stageTimes": self.stage_times,
            "quantile": dict([(k, int(v.total_seconds() * 1000000)) for k, v in self.quantile.items()])
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
        res.stages = [UnitStageResult.from_json(i) for i in obj["stages"]]
        res.stage_milliseconds = obj["stageMilliseconds"]
        res.stageTimes = obj["stageTimes"]
        res.quantile = dict([(k, timedelta(microseconds=v)) for k, v in obj["quantile"].items()])
        return res

    def __init__(
        self, name, parallel, limit, err_message=None,
        stage_seconds=0, stage_times=0, stage_number=100,
        quantile=None, max_step_size=200000,
    ):
        self.quantile_keys = quantile
        if self.quantile_keys is None:
            self.quantile_keys = [80, 90, 95, 99, 99.9]
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
        self.stages = list[UnitStageResult]()
        self.stage_milliseconds = stage_seconds * 1000 // stage_number
        if self.stage_milliseconds < 100:
            self.stage_milliseconds = 100
        self.stage_times = stage_times // stage_number
        self.current_stage = UnitStageResult()
        self.max_step_size = max_step_size
        self.steps = list[StepResult]()
        self.quantile = dict()

    def add_step_result(self, result: StepResult):
        self.total += 1
        if result.success:
            self.success += 1
            self.elapse += result.elapse
        else:
            if result.code not in self.code:
                self.code[result.code] = 0
            self.code[result.code] += 1

        self.current_stage.add_step_result(result)
        if self.stage_milliseconds != 0 and (datetime.now() - self.current_stage.time).total_seconds() * 1000 >= self.stage_milliseconds:
            self.current_stage.summary()
            self.stages.append(self.current_stage)
            self.current_stage = UnitStageResult()
        if self.stage_times != 0 and self.current_stage.total >= self.stage_times:
            self.current_stage.summary()
            self.stages.append(self.current_stage)
            self.current_stage = UnitStageResult()

        if self.max_step_size == 0:
            self.steps.append(result)
        elif self.max_step_size > len(self.steps):
            self.steps.append(result)
        else:
            self.steps[random.randint(0, len(self.steps))] = result

    def summary(self):
        self.end_time = datetime.now()
        self.total_elapse = self.end_time - self.start_time
        self.qps = self.success / self.total_elapse.total_seconds()
        if self.success != 0:
            self.res_time = self.elapse / self.success
        if self.total != 0:
            self.rate = self.success / self.total
        self.code["OK"] = self.success

        self.steps.sort(key=lambda x: x.elapse)
        self.quantile = dict([(k, self.steps[int(len(self.steps) * k // 100)].elapse) for k in self.quantile_keys])

        self.current_stage.summary()
        self.stages.append(self.current_stage)


@dataclass
class UnitGroup:
    idx: int
    seconds: int
    times: int
    units: list[UnitResult]
    quantile: list

    def to_json(self):
        return {
            "idx": self.idx,
            "seconds": self.seconds,
            "times": self.times,
            "units": self.units,
            "quantile": self.quantile
        }

    @staticmethod
    def from_json(obj):
        res = UnitGroup(obj["idx"], obj["seconds"], obj["times"], quantile=obj["quantile"])
        res.idx = obj["idx"]
        res.seconds = obj["seconds"]
        res.times = obj["times"]
        res.units = [UnitResult.from_json(i) for i in obj["units"]]
        return res

    def __init__(self, idx, seconds, times, quantile=None):
        self.quantile = quantile
        if self.quantile is None:
            self.quantile = [80, 90, 95, 99, 99.9]
        self.idx = idx
        self.seconds = seconds
        self.times = times
        self.units = list[UnitResult]()

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
        return res

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
            "subTests": self.sub_tests,
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
        res.sub_tests = [TestResult.from_json(i) for i in obj["subTests"]]
        return res

    def __init__(self, id_, directory, name, description="", err_message=None):
        self.id_ = id_
        self.directory = directory
        self.name = name
        self.description = description
        self.is_err = False
        self.err = ""
        self.plans = list[PlanResult]()
        self.sub_tests = list[TestResult]()
        if err_message:
            self.is_err = True
            self.err = err_message

    def add_plan_result(self, plan):
        self.plans.append(plan)

    def add_sub_test_result(self, sub_test):
        self.sub_tests.append(sub_test)
