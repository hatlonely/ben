#!/usr/bin/env python3


import concurrent.futures
import copy
import json
import uuid
import os
import yaml
import pathlib
import sys
import queue
import importlib
from types import SimpleNamespace
from dataclasses import dataclass
from datetime import datetime
from itertools import repeat

from ..seed import seed_map
from ..util import merge, REQUIRED, render
from ..driver import Driver, driver_map
from ..reporter import Reporter, reporter_map
from ..result import TestResult, PlanResult, UnitResult, StepResult


@dataclass
class RuntimeConstant:
    test_id: str
    test_directory: str
    plan_directory: str
    driver_map: dict
    x: any


@dataclass
class RuntimeContext:
    ctx: dict[str, Driver]
    var: SimpleNamespace
    var_info: dict


class Framework:
    def __init__(
        self,
        test_directory=None,
        plan_directory=None,
        customize=None,
        reporter="text",
        x=None,
        json_result=None,
    ):

        self.seed_map = seed_map
        self.reporter_map = reporter_map
        self.driver_map = driver_map
        self.x = None
        if x:
            self.x = Framework.load_x(x)
            if hasattr(self.x, "reporter_map"):
                self.reporter_map = self.reporter_map | self.x.reporter_map
            if hasattr(self.x, "seed_map"):
                self.seed_map = self.seed_map | self.x.seed_map
            if hasattr(self.x, "driver_map"):
                self.driver_map = self.driver_map | self.x.driver_map

        self.constant = RuntimeConstant(
            test_id=uuid.uuid4().hex,
            test_directory=test_directory,
            plan_directory=test_directory if not plan_directory else os.path.join(test_directory, plan_directory.strip().rstrip("/")),
            driver_map=self.driver_map,
            x=self.x,
        )

        if not customize and os.path.exists(os.path.join(pathlib.Path.home(), ".ben/customize.yaml")):
            customize = os.path.join(pathlib.Path.home(), ".ben/customize.yaml")

        cfg = {}
        if customize:
            with open(customize, "r", encoding="utf-8") as fp:
                cfg = yaml.safe_load(fp)
        cfg = merge(cfg, {
            "reporter": {
                reporter: {
                    "i18n": {}
                }
            },
            "framework": {
                "keyPrefix": {
                    "eval": "#",
                    "exec": "%",
                    "loop": "!",
                    "shell": "$",
                },
                "loadingFiles": {
                    "ctx": "ctx.yaml",
                    "var": "var.yaml",
                    "description": "README.md",
                }
            }
        })
        cfg = render(
            cfg,
            peval=cfg["framework"]["keyPrefix"]["eval"],
            pexec=cfg["framework"]["keyPrefix"]["exec"],
            pshell=cfg["framework"]["keyPrefix"]["shell"],
        )

        self.customize = json.loads(json.dumps(cfg["framework"]), object_hook=lambda y: SimpleNamespace(**y))
        self.reporter = self.reporter_map[reporter](cfg["reporter"][reporter])
        self.json_result = json_result

    def format(self):
        pass

    def run(self):
        rctx = RuntimeContext(
            ctx={},
            var=None,
            var_info={},
        )

        res = Framework.run_test(self.constant.test_directory, self.customize, self.constant, rctx)
        print(self.reporter.report(res))

    @staticmethod
    def run_test(
        directory: str,
        customize,
        constant: RuntimeConstant,
        parent_ctx: RuntimeContext,
    ):
        info = Framework.load_ctx(os.path.basename(directory), os.path.join(directory, customize.loadingFiles.ctx))
        description = info["description"] + Framework.load_description(os.path.join(directory, customize.loadingFiles.description))
        var_info = copy.deepcopy(parent_ctx.var_info) | info["var"] | Framework.load_var(os.path.join(directory, customize.loadingFiles.var))
        var_info = render(var_info, peval=customize.keyPrefix.eval, pexec=customize.keyPrefix.exec, pshell=customize.keyPrefix.shell)
        var = json.loads(json.dumps(var_info), object_hook=lambda x: SimpleNamespace(**x))
        ctx = copy.copy(parent_ctx.ctx)
        for key in info["ctx"]:
            val = merge(info["ctx"][key], {
                "type": REQUIRED,
                "args": {}
            })
            val = render(val, var=var, x=constant.x, peval=customize.keyPrefix.eval, pexec=customize.keyPrefix.exec, pshell=customize.keyPrefix.shell)
            ctx[key] = constant.driver_map[val["type"]](val["args"])

        test_result = TestResult(
            constant.test_id,
            directory,
            info["name"],
            description=description,
        )

        rctx = RuntimeContext(
            ctx=ctx,
            var=var,
            var_info=var_info,
        )

        if directory.startswith(constant.plan_directory):
            for plan_info in Framework.plans(customize, constant, info, directory):
                result = Framework.run_plan(directory, customize, constant, rctx, plan_info)
                test_result.add_plan_result(result)

        for sub_directory in [os.path.join(directory, i) for i in os.listdir(directory) if os.path.isdir(os.path.join(directory, i))]:
            result = Framework.run_test(sub_directory, customize, constant, rctx)
            test_result.add_sub_test_result(result)

        return test_result

    @staticmethod
    def run_plan(
        directory,
        customize,
        constant: RuntimeConstant,
        rctx: RuntimeContext,
        plan_info
    ):
        plan_info = merge(plan_info, {
            "name": directory,
            "terminal": {
                "seconds": 3
            },
            "unit": []
        })
        print(plan_info["unit"])
        plan_result = PlanResult(plan_info["planID"])
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(plan_info["unit"]))
        results = pool.map(Framework.run_unit, repeat(customize), repeat(constant), repeat(rctx), [i for i in plan_info["unit"]])
        for result in results:
            plan_result.add_unit_result(result)

        return plan_result

    @staticmethod
    def run_unit(
        customize,
        constant: RuntimeConstant,
        rctx: RuntimeContext,
        unit_info,
    ):
        unit_info = merge(unit_info, {
            "parallel": 1,
            "qps": 0,
            "step": REQUIRED,
        })
        print(unit_info)
        unit_result = UnitResult()
        return unit_result

        q = queue.Queue(maxsize=unit_info["parallel"])
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=unit_info["parallel"])
        pool.submit(Framework.run_steps, customize, constant, rctx, plan, unit_info, queue)
        success = 0
        while True:
            # terminal
            item = q.get()
            success += 1
        return success

    @staticmethod
    def run_steps(
        customize,
        constant: RuntimeConstant,
        rctx: RuntimeContext,
        plan, seed, step_infos, q: queue.Queue
    ):
        ress = []
        for step_info in step_infos:
            res = Framework.run_step(
                customize,
                constant,
                rctx,
                plan, seed, step_info
            )
            ress.append(res)
        q.put(ress)

    @staticmethod
    def run_step(
        customize,
        constant: RuntimeConstant,
        rctx: RuntimeContext,
        plan, unit, seed,
        step_info,
    ):
        step_result = StepResult()
        step_start = datetime.now()
        req = render(step_info["req"], plan=plan, unit=unit, seed=seed, var=rctx.var, x=constant.x)
        res = rctx.ctx[step_info["ctx"]].do(req)
        print(res)
        return step_result

    @staticmethod
    def plans(customize, constant: RuntimeConstant, info, directory):
        for idx, plan in enumerate(info["plan"]):
            yield Framework.format_plan(plan, customize.loadingFiles.ctx, idx)

        for filename in [
            i
            for i in os.listdir(directory)
            if i not in [
                customize.loadingFiles.ctx,
                customize.loadingFiles.var,
                customize.loadingFiles.description,
            ]
            and os.path.isfile(os.path.join(directory, i))
        ]:
            if not filename.endswith(".yaml"):
                continue
            for plan in Framework.load_plan(directory, filename):
                yield plan

    @staticmethod
    def load_ctx(name, filename):
        dft = {
            "name": name,
            "description": "",
            "var": {},
            "ctx": {},
            "seed": {},
            "plan": [],
        }
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return dft
        with open(filename, "r", encoding="utf-8") as fp:
            info = yaml.safe_load(fp)
        return merge(info, dft)

    @staticmethod
    def load_description(filename):
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return ""
        with open(filename, "r", encoding="utf-8") as fp:
            info = fp.readlines()
        return info

    @staticmethod
    def load_x(filename):
        if not os.path.exists(filename) or not os.path.isdir(filename):
            return {}
        p = pathlib.Path(filename)
        sys.path.append(str(p.parent.absolute()))
        return importlib.import_module(str(p.name), "x")

    @staticmethod
    def load_var(filename):
        if not os.path.exists(filename) or not os.path.isfile(filename):
            return {}
        with open(filename, "r", encoding="utf-8") as fp:
            info = yaml.safe_load(fp)
        return info

    @staticmethod
    def load_plan(directory, filename):
        with open(os.path.join(directory, filename), "r", encoding="utf-8") as fp:
            info = yaml.safe_load(fp)
            if isinstance(info, dict):
                yield Framework.format_plan(info, filename, 0)
            if isinstance(info, list):
                for idx, item in enumerate(info):
                    yield Framework.format_plan(item, filename, idx)

    @staticmethod
    def format_plan(info, filename, idx):
        text = os.path.splitext(filename)[0]
        plan_id = "{}-{}".format(text, idx)
        if idx == 0 and text.rfind("-") == -1:
            plan_id = text
        info = merge(info, {
            "name": REQUIRED,
            "description": "",
            "planID": plan_id
        })
        return info
