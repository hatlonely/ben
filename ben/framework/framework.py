#!/usr/bin/env python3
import copy
import json
import os
import yaml
import pathlib
import sys
import importlib
from types import SimpleNamespace
from dataclasses import dataclass

from ..seed import seed_map
from ..util import merge, REQUIRED, render
from ..driver import Driver
from ..reporter import Reporter, reporter_map


@dataclass
class RuntimeConstant:
    x: any
    driver_map: dict


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
        reporter=None,
        x=None,
        json_result=None,
    ):
        self.constant = RuntimeConstant(
            x=x,
        )

        self.seed_map = seed_map
        self.reporter_map = reporter_map
        if x:
            self.x = Framework.load_x(x)
            if hasattr(self.x, "reporter_map"):
                self.reporter_map = self.reporter_map | self.x.reporter_map
            if hasattr(self.x, "seed_map"):
                self.seed_map = self.seed_map | self.x.seed_map

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
        pass

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

    def run_plan(self):
        pass

    @staticmethod
    def load_ctx(name, filename):
        dft = {
            "name": name,
            "description": "",
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
