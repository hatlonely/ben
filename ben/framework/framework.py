#!/usr/bin/env python3


import concurrent.futures
import copy
import json
import traceback
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

from ..util import merge, REQUIRED, render
from ..seed import seed_map, Seed
from ..driver import Driver, driver_map
from ..reporter import reporter_map
from ..hook import Hook, hook_map
from ..monitor import Monitor, monitor_map
from ..result import TestResult, PlanResult, UnitGroup, UnitResult, StepResult, SubStepResult
from .stop import Stop


@dataclass
class RuntimeConstant:
    test_id: str
    test_directory: str
    plan_directory: str
    driver_map: dict
    seed_map: dict
    monitor_map: dict
    hooks: list[Hook]
    x: any


@dataclass
class RuntimeContext:
    ctx: dict[str, Driver]
    var: SimpleNamespace
    var_info: dict
    seed: dict[str, Seed]


class Framework:
    def __init__(
        self,
        test_directory=None,
        plan_directory=None,
        customize=None,
        reporter="text",
        x=None,
        json_result=None,
        hook=None,
        lang=None,
    ):

        self.seed_map = seed_map
        self.reporter_map = reporter_map
        self.driver_map = driver_map
        self.hook_map = hook_map
        self.monitor_map = monitor_map
        self.x = None
        if x:
            self.x = Framework.load_x(x)
            if hasattr(self.x, "reporter_map"):
                self.reporter_map = self.reporter_map | self.x.reporter_map
            if hasattr(self.x, "seed_map"):
                self.seed_map = self.seed_map | self.x.seed_map
            if hasattr(self.x, "driver_map"):
                self.driver_map = self.driver_map | self.x.driver_map
            if hasattr(self.x, "hook_map"):
                self.hook_map = self.hook_map | self.x.hook_map
            if hasattr(self.x, "monitor_map"):
                self.monitor_map = self.monitor_map | self.x.monitor_map

        if not customize and os.path.exists(os.path.join(pathlib.Path.home(), ".ben/customize.yaml")):
            customize = os.path.join(pathlib.Path.home(), ".ben/customize.yaml")

        hooks = hook.split(",") if hook else []
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
            "hook": dict([(i, {"i18n": {}}) for i in hooks]),
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

        if "i18n" in cfg:
            cfg["reporter"][reporter] = merge(cfg["reporter"][reporter], cfg["i18n"])
            for key in hooks:
                cfg["hook"][key] = merge(cfg["hook"][key], cfg["i18n"])
        if lang:
            cfg["reporter"][reporter]["lang"] = lang
            for key in hooks:
                cfg["hook"][key]["lang"] = lang

        self.customize = json.loads(json.dumps(cfg["framework"]), object_hook=lambda y: SimpleNamespace(**y))
        self.reporter = self.reporter_map[reporter](cfg["reporter"][reporter])
        self.json_result = json_result
        self.hooks = [self.hook_map[i](cfg["hook"][i], test_id=self.constant.test_id) for i in hooks]

        self.constant = RuntimeConstant(
            test_id=uuid.uuid4().hex,
            test_directory=test_directory,
            plan_directory=test_directory if not plan_directory else os.path.join(test_directory, plan_directory.strip().rstrip("/")),
            driver_map=self.driver_map,
            seed_map=self.seed_map,
            monitor_map=self.monitor_map,
            x=self.x,
            hooks=self.hooks,
        )

    def format(self):
        res = TestResult.from_json(json.load(open(self.json_result)))
        print(self.reporter.report(res))

    def run(self):
        context = RuntimeContext(
            ctx={},
            var=None,
            var_info={},
            seed={},
        )

        res = Framework.must_run_test(self.constant.test_directory, self.customize, self.constant, context)
        print(self.reporter.report(res))

    @staticmethod
    def must_run_test(
        directory: str,
        customize,
        constant: RuntimeConstant,
        context: RuntimeContext,
    ):
        for hook in constant.hooks:
            hook.on_test_start(directory)

        try:
            result = Framework.run_test(directory, customize, constant, context)
        except Exception as e:
            result = TestResult(constant.test_id, directory, directory, "", "Exception {}".format(traceback.format_exc()))

        for hook in constant.hooks:
            hook.on_test_end(result)
        return result

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
        seed = dict([(k, v) for k, v in parent_ctx.seed.items()])
        for key in info["seed"]:
            val = merge(info["seed"][key], {
                "type": REQUIRED,
                "args": {}
            })
            val = render(val, var=var, x=constant.x, peval=customize.keyPrefix.eval, pexec=customize.keyPrefix.exec, pshell=customize.keyPrefix.shell)
            seed[key] = constant.seed_map[val["type"]](val["args"])

        test_result = TestResult(
            constant.test_id,
            directory,
            info["name"],
            description=description,
        )

        context = RuntimeContext(
            ctx=ctx,
            var=var,
            var_info=var_info,
            seed=seed,
        )

        if directory.startswith(constant.plan_directory):
            for plan_info in Framework.plans(customize, constant, info, directory):
                result = Framework.must_run_plan(directory, customize, constant, context, plan_info)
                test_result.add_plan_result(result)

        for sub_directory in [os.path.join(directory, i) for i in os.listdir(directory) if os.path.isdir(os.path.join(directory, i))]:
            result = Framework.must_run_test(sub_directory, customize, constant, context)
            test_result.add_sub_test_result(result)

        return test_result

    @staticmethod
    def must_run_plan(
        directory,
        customize,
        constant: RuntimeConstant,
        context: RuntimeContext,
        plan_info
    ):
        for hook in constant.hooks:
            hook.on_plan_start(plan_info)

        try:
            result = Framework.run_plan(directory, customize, constant, context, plan_info)
        except Exception as e:
            result = PlanResult(plan_info["planID"], plan_info["name"], "Exception {}".format(traceback.format_exc()))

        for hook in constant.hooks:
            hook.on_plan_end(result)
        return result

    @staticmethod
    def run_plan(
        directory,
        customize,
        constant: RuntimeConstant,
        context: RuntimeContext,
        plan_info
    ):
        plan_info = merge(plan_info, {
            "group": [],
            "unit": [],
            "monitor": {},
        })

        plan_result = PlanResult(plan_info["planID"], plan_info["name"])
        for idx, group in enumerate(plan_info["group"]):
            group = merge(group, {
                "seconds": 0,
                "times": 0,
                "quantile": [80, 90, 95, 99, 99.9],
                "maxStepSize": 200000,
            })

            monitors = dict[str, Monitor]()
            for key, info in plan_info["monitor"].items():
                val = merge(info, {
                    "type": REQUIRED,
                    "args": {}
                })
                val = render(val, var=context.var, x=constant.x, peval=customize.keyPrefix.eval, pexec=customize.keyPrefix.exec, pshell=customize.keyPrefix.shell)
                monitors[key] = constant.monitor_map[val["type"]](val["args"])
            for _, m in monitors.items():
                m.collect()

            start = datetime.now()
            stop = Stop(group)
            pool = concurrent.futures.ThreadPoolExecutor(max_workers=len(plan_info["unit"]))
            results = pool.map(
                Framework.must_run_unit,
                repeat(customize),
                repeat(constant),
                repeat(context),
                repeat(stop),
                repeat(1) if "parallel" not in group else [i for i in group["parallel"]],
                repeat(0) if "limit" not in group else [i for i in group["limit"]],
                repeat(group),
                [i for i in plan_info["unit"]],
            )
            unit_group = UnitGroup(idx, group["seconds"], group["times"], quantile=group["quantile"])
            for result in results:
                unit_group.add_unit_result(result)
            end = datetime.now()
            for k, m in monitors.items():
                unit_group.add_monitor_stat(k, m.unit(), m.stat(start, end))
            plan_result.add_unit_group(unit_group)
        return plan_result

    @staticmethod
    def must_run_unit(
        customize,
        constant: RuntimeConstant,
        context: RuntimeContext,
        stop: Stop,
        parallel,
        limit,
        group_info,
        unit_info,
    ):
        unit_info = merge(unit_info, {"name": "unit"})

        for hook in constant.hooks:
            hook.on_unit_start(unit_info)

        try:
            result = Framework.run_unit(customize, constant, context, stop, parallel, limit, group_info, unit_info)
        except Exception as e:
            result = UnitResult(unit_info["name"], parallel, limit, err_message="Exception {}".format(traceback.format_exc()))

        for hook in constant.hooks:
            hook.on_unit_end(result)
        return result

    @staticmethod
    def run_unit(
        customize,
        constant: RuntimeConstant,
        context: RuntimeContext,
        stop: Stop,
        parallel,
        limit,
        group_info,
        unit_info,
    ):
        unit_info = merge(unit_info, {
            "seed": {},
            "step": [],
        })

        q = queue.Queue(maxsize=parallel)
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=parallel)
        for i in range(parallel):
            pool.submit(
                Framework.must_run_step,
                customize,
                constant,
                context,
                stop,
                unit_info["seed"],
                unit_info["step"],
                q,
            )
        unit_result = UnitResult(
            unit_info["name"], parallel, limit,
            stage_seconds=stop.seconds, stage_times=stop.times,
            quantile=group_info["quantile"], max_step_size=group_info["maxStepSize"],
        )
        while stop.is_running() or not q.empty():
            step_result = q.get()
            unit_result.add_step_result(step_result)
        unit_result.summary()
        return unit_result

    @staticmethod
    def must_run_step(
        customize,
        constant: RuntimeConstant,
        context: RuntimeContext,
        stop: Stop,
        seed_info,
        step_info,
        q: queue.Queue,
    ):
        while stop.next():
            for hook in constant.hooks:
                hook.on_step_start(step_info)

            try:
                result = Framework.run_step(customize, constant, context, seed_info, step_info)
            except Exception as e:
                result = StepResult()
            q.put(result)

            for hook in constant.hooks:
                hook.on_step_end(step_info)

    @staticmethod
    def run_step(
        customize,
        constant: RuntimeConstant,
        context: RuntimeContext,
        seed_info,
        step_info,
    ):
        step_result = StepResult()
        seed = dict([(k, context.seed[v].pick()) for k, v in seed_info.items()])
        for idx, info in enumerate(step_info):
            info = merge(info, {
                "name": "step-{}".format(idx),
            })
            name = info["name"]
            try:
                info = merge(info, {
                    "ctx": REQUIRED,
                    "req": REQUIRED,
                    "res": REQUIRED,
                })
                req = render(info["req"], seed=seed, var=context.var, x=constant.x, peval=customize.keyPrefix.eval, pexec=customize.keyPrefix.exec, pshell=customize.keyPrefix.shell)
                name = context.ctx[info["ctx"]].name(req)
                ts = datetime.now()
                res = context.ctx[info["ctx"]].do(req)
                elapse = datetime.now() - ts

                render_res = render(info["res"], res=res, seed=seed, var=context.var, x=constant.x, peval=customize.keyPrefix.eval, pexec=customize.keyPrefix.exec, pshell=customize.keyPrefix.shell)
                step_result.add_sub_step_result(SubStepResult(
                    req=req,
                    res=res,
                    name=name,
                    code=render_res["groupby"],
                    success=render_res["groupby"] == render_res["success"],
                    elapse=elapse,
                ))
            except Exception as e:
                step_result.add_err_result(name, "Exception {}".format(traceback.format_exc()))
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
            "name": plan_id,
            "description": "",
            "planID": plan_id
        })
        return info
