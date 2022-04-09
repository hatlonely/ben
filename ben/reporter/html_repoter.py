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
    <title>{{ test.name }} {{ i18n.title.report }}</title>
    <meta charset="UTF-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-ka7Sk0Gln4gmtz2MlQnikT1wXgYsOg+OMhuP+IlRH9sENBO0LRn5q+8nbTov4+1p" crossorigin="anonymous"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.8.1/font/bootstrap-icons.css">
    <script src="https://code.jquery.com/jquery-3.6.0.slim.min.js" integrity="sha256-u7e5khyithlIdTpu22PHhENmPcRdFiHRjhAuHcs05RI=" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.3.2/dist/echarts.min.js" integrity="sha256-7rldQObjnoCubPizkatB4UZ0sCQzu2ePgyGSUcVN70E=" crossorigin="anonymous"></script>

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
            {{ render_test(test, "test") }}
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
<div class="col-md-12" id={{ name }}>
    {% if test.is_err %}
    <div class="card my-{{ customize.padding.y }} border-danger">
        <h5 class="card-header text-white bg-danger">{{ i18n.title.test }} {{ test.name }} {{ i18n.status.fail }}</h5>
    {% else %}
    <div class="card my-{{ customize.padding.y }} border-success">
        <h5 class="card-header text-white bg-success">{{ i18n.title.test }} {{ test.name }} {{ i18n.status.succ }}</h5>
    {% endif %}

        {# render err #}
        {% if test.is_err %}
        <div class="card-header text-white bg-danger"><span class="fw-bolder">{{ i18n.test.err }}</span></div>
        <div class="card-body"><pre>{{ test.err }}</pre></div>
        {% endif %}

        {# render description #}
        {% if test.description %}
        <div class="card-header justify-content-between d-flex"><span class="fw-bolder">{{ i18n.testHeader.description }}</span></div>
        <div class="card-body">{{ markdown(test.description) }}</div>
        {% endif %}

        {# render plan #}
        {% if test.plans %}
        <div class="card-header justify-content-between d-flex">
            <span class="fw-bolder">{{ i18n.title.plan }}</span>
        </div>
        <ul class="list-group list-group-flush" id="{{ name }}-plan">
            {% for plan in test.plans %}
            <li class="list-group-item px-{{ customize.padding.x }} py-{{ customize.padding.y }} plan">
                {{ render_plan(plan, '{}-plan-{}'.format(name, loop.index0)) }}
            </li>
            {% endfor %}
        </ul>
        {% endif %}
    </div>
</div>
"""

_plan_tpl = """
<a class="card-title btn d-flex justify-content-between align-items-center" data-bs-toggle="collapse" href="#{{ name }}" role="button" aria-expanded="false" aria-controls="{{ name }}">
    {{ plan.name }}
</a>
<div class="collapse card" id="{{ name }}">
    {% if plan.is_err %}
    <div class="card border-danger">
    {% else %}
    <div class="card border-success">
    {% endif %}
    
        {# Description #}
        {% if plan.description %}
        <div class="card-header"><span class="fw-bolder">{{ i18n.title.description }}</span></div>
        <div class="card-body">{{ markdown(plan.description) }}</div>
        {% endif %}
    
        {# Command #}
        {% if plan.command %}
        <div class="card-header"><span class="fw-bolder">{{ i18n.title.command }}</span></div>
        <div class="card-body">
            <div class="float-end">
                <button type="button" class="btn btn-sm py-0" onclick="copyToClipboard('{{ name }}-command')"
                    data-bs-toggle="tooltip" data-bs-placement="top" title="{{ i18n.toolTips.copy }}">
                    <i class="bi-clipboard"></i>
                </button>
            </div>
            <span id="{{ name }}-command">{{ plan.command }}</span>
        </div>
        {% endif %}
    
        {# UnitGroup #}
        {% if plan.unit_groups %}
        <ul class="list-group list-group-flush">
            {% for unit_group in plan.unit_groups %}
            <li class="list-group-item px-{{ customize.padding.x }} py-{{ customize.padding.y }}">
                {{ render_unit_group(unit_group, '{}-group-{}'.format(name, loop.index0)) }}
            </li>
            {% endfor %}
        </ul>
        {% endif %}
    </div>
</div>
"""

_unit_group_tpl = """
<div class="card" id="{{ name }}">
    {% if group.is_err %}<div class="card border-danger">{% else %}<div class="card border-success">{% endif %}

    <div class="card-body">
        <table class="table table-striped">
            <thead>
                <tr class="text-center">
                    <th>{{ i18n.title.seconds }}</th>
                    <th>{{ i18n.title.times }}</th>
                    <th>{{ i18n.title.unit }}</th>
                    <th>{{ i18n.title.parallel }}</th>
                    <th>{{ i18n.title.limit }}</th>
                    <th>{{ i18n.title.total }}</th>
                    <th>{{ i18n.title.rate }}</th>
                    <th>{{ i18n.title.qps }}</th>
                    <th>{{ i18n.title.resTime }}</th>
                </tr>
            </thead>
            <tbody>
                {% for unit in group.units %}
                <tr class="text-center">
                    <td>{{ group.seconds }}</td>
                    <td>{{ group.times }}</td>
                    <td>{{ unit.name }}</td>
                    <td>{{ unit.parallel }}</td>
                    <td>{{ unit.limit }}</td>
                    <td>{{ unit.total }}</td>
                    <td>{{ int(unit.rate * 10000) / 100 }}%</td>
                    <td>{{ int(unit.qps) }}</td>
                    <td>{{ format_timedelta(unit.res_time) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    {# Code #}
    <div class="card-header justify-content-between d-flex"><span class="fw-bolder">{{ i18n.title.code }}</span></div>
    <div class="card-body d-flex justify-content-center">
        {% for unit in group.units %}
        {% if unit.code %}
        <div id="{{ '{}-unit-{}'.format(name, loop.index0) }}" style="width: 300px;height:300px;"></div>
        <script>
            echarts.init(document.getElementById("{{ '{}-unit-{}'.format(name, loop.index0) }}")).setOption({
              tooltip: {
                trigger: "item"
              },
              series: [
                {
                  name: "{{ unit.name }}",
                  type: "pie",
                  radius: ['40%', '70%'],
                  avoidLabelOverlap: false,
                  label: {
                    show: false,
                    position: 'center'
                  },
                  emphasis: {
                    label: {
                      show: true,
                      fontSize: '20',
                      fontWeight: 'bold'
                    }
                  },
                  labelLine: {
                    show: false
                  },
                  data: {{ json.dumps(dict_to_items(unit.code)) }}
                }
              ]
            });
        </script>
        {% endif %}
        {% endfor %}
    </div>
</div>
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
        env.globals.update(dict_to_items=HtmlReporter.dict_to_items)
        env.globals.update(json=json, int=int, list=list)
        env.globals.update(render_test=self.render_test)
        env.globals.update(render_plan=self.render_plan)
        env.globals.update(render_unit_group=self.render_unit_group)
        env.globals.update(markdown=markdown.markdown)
        env.globals.update(i18n=self.i18n)
        env.globals.update(customize=self.customize)
        self.report_tpl = env.from_string(_report_tpl)
        self.test_tpl = env.from_string(_test_tpl)
        self.plan_tpl = env.from_string(_plan_tpl)
        self.unit_group_tpl = env.from_string(_unit_group_tpl)

    def report(self, test: TestResult) -> str:
        return self.report_tpl.render(test=test)

    def render_test(self, test, name):
        return self.test_tpl.render(test=test, name=name)

    def render_plan(self, plan, name):
        return self.plan_tpl.render(plan=plan, name=name)

    def render_unit_group(self, unit_group, name):
        return self.unit_group_tpl.render(group=unit_group, name=name)

    @staticmethod
    def format_timedelta(t: datetime.timedelta):
        if t >= datetime.timedelta(seconds=1):
            return "{:.3f}s".format(t.total_seconds())
        return "{:.3f}ms".format(t.total_seconds()*1000)

    @staticmethod
    def dict_to_items(d: dict):
        return list([({"name": k, "value": v}) for k, v in d.items()])
