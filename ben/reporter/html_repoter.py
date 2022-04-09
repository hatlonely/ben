#!/usr/bin/env python3


import datetime
import json
from jinja2 import Environment, BaseLoader
import markdown
from types import SimpleNamespace

from ..util import merge, REQUIRED
from .reporter import Reporter
from ..result import TestResult


_report_tpl = """<!DOCTYPE html>
<html lang="zh-cmn-Hans">
<head>
    <title>{{ res.name }} {{ i18n.title.report }}</title>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    {{ customize.font.style }}
    <style>
        body {
            font-family: {{ customize.font.body }};
        }
        pre, code {
            font-family: {{ customize.font.code }};
        }
    </style>

    {{ customize.extra.head }}
</head>

<body>
    {{ customize.extra.bodyHeader }}
    <div class="container">
        <div class="row justify-content-md-center">
            <div class="col-lg-10 col-md-12">
            {{ render_test(res, "test") }}
            </div>
        </div>
    </div>
    {{ customize.extra.bodyFooter }}
</body>
<script>
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl)
    })
</script>
</html>
"""

_test_tpl = """

"""

_plan_tpl = """

"""

_unit_group_tpl = """
"""

_unit_tpl = """
"""


class HtmlReporter(Reporter):
    def __init__(self, args=None):
        super().__init__(args)
        args = merge(args, {
            "stepSeparator": "#",
            "font": {
                "style": """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono&family=Roboto+Condensed:wght@400;700&display=swap" rel="stylesheet">
""",
                "body": "'Roboto Condensed', sans-serif !important",
                "code": "'JetBrains Mono', monospace !important",
            },
            "extra": {
                "head": "",
                "bodyHeader": "",
                "bodyFooter": "",
            },
            "padding": {
                "x": 2,
                "y": 2,
            }
        })
        self.step_separator = args["stepSeparator"]
        self.customize = json.loads(json.dumps(args), object_hook=lambda x: SimpleNamespace(**x))

        env = Environment(loader=BaseLoader())
        env.globals.update(format_timedelta=HtmlReporter.format_timedelta)
        env.globals.update(json=json)
        env.globals.update(render_test=self.render_test)
        env.globals.update(render_plan=self.render_plan)
        env.globals.update(render_unit_group=self.render_unit_group)
        env.globals.update(render_unit=self.render_unit)
        env.globals.update(markdown=markdown.markdown)
        env.globals.update(i18n=self.i18n)
        env.globals.update(customize=self.customize)
        self.report_tpl = env.from_string(_report_tpl)
        self.test_tpl = env.from_string(_test_tpl)
        self.plan_tpl = env.from_string(_plan_tpl)
        self.unit_group_tpl = env.from_string(_unit_group_tpl)
        self.unit_tpl = env.from_string(_unit_tpl)

    def report(self, test: TestResult) -> str:
        return self.report_tpl.render(test=test)

    def render_test(self, test, name):
        return self.test_tpl.render(test=test, name=name)

    def render_plan(self, plan, name):
        return self.plan_tpl.render(plan=plan, name=name)

    def render_unit_group(self, unit_group, name):
        return self.unit_group_tpl.render(group=unit_group, name=name)

    def render_unit(self, unit, name):
        return self.unit_tpl.render(unit=unit, name=name)

    @staticmethod
    def format_timedelta(t: datetime.timedelta):
        return "{:.3f}s".format(t.total_seconds())
