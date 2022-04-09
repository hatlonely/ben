#!/usr/bin/env python3
import durationpy

from .reporter import Reporter
from ..result import TestResult, PlanResult, UnitGroup, UnitResult
from ..util import merge


class TextReporter(Reporter):
    def __init__(self, args):
        super().__init__(args)
        args = merge(args, {
            "padding": "  "
        })
        self.padding_to_add = args["padding"]
        self.padding = ""

    def report(self, res: TestResult) -> str:
        return "\n".join(self._format_test(res))

    def _format_test(self, res: TestResult) -> list[str]:
        lines = ["{}{i18n.title.test} {res.name}".format(self.padding, res=res, i18n=self.i18n)]
        if res.is_err:
            lines.extend([
                "{}{}{}".format(self.padding_to_add, self.padding, line)
                for line in "{i18n.title.err} {res.err}".format(res=res, i18n=self.i18n).split("\n")
            ])
            return lines
        self.padding += self.padding_to_add
        for plan in res.plans:
            lines.extend([self.padding + i for i in self._format_plan(plan)])
        for sub_test in res.sub_tests:
            lines.extend([self.padding + i for i in self._format_test(sub_test)])
        self.padding = self.padding[:-len(self.padding_to_add)]
        lines.append("{}{i18n.title.test} {res.name}".format(self.padding, res=res, i18n=self.i18n))
        return lines

    def _format_plan(self, res: PlanResult) -> list[str]:
        lines = ["{}{i18n.title.plan} {res.name}".format(self.padding, res=res, i18n=self.i18n)]
        if res.is_err:
            lines.extend([
                "{}{}{}".format(self.padding_to_add, self.padding, line)
                for line in "{i18n.title.err} {res.err}".format(res=res, i18n=self.i18n).split("\n")
            ])
            return lines
        for unit_group in res.unit_groups:
            lines.extend([self.padding + i for i in self._format_unit_group(unit_group)])
        lines.append("{}{i18n.title.plan} {res.name}".format(self.padding, res=res, i18n=self.i18n))
        return lines

    def _format_unit_group(self, res: UnitGroup):
        lines = [
            "{}{i18n.title.unitGroup} "
            "{i18n.title.idx}: {res.idx}, "
            "{i18n.title.seconds}: {res.seconds}, "
            "{i18n.title.times}: {res.times}".format(self.padding, res=res, i18n=self.i18n)
        ]
        for unit in res.units:
            lines.extend([self.padding + i for i in self._format_unit(unit)])
        return lines

    def _format_unit(self, res: UnitResult) -> list[str]:
        lines = [
            "{}{i18n.title.unit} {res.name} "
            "{i18n.title.parallel}: {res.parallel}, "
            "{i18n.title.limit}: {res.limit}, "
            "{i18n.title.total}: {res.total}, "
            "{i18n.title.rate}: {rate}%, "
            "{i18n.title.qps}: {qps}, "
            "{i18n.title.resTime}: {res_time}, "
            "".format(
                self.padding, res=res, i18n=self.i18n,
                res_time=durationpy.to_str(res.res_time),
                qps=int(res.qps),
                rate=int(res.rate * 10000) / 100.0
            )
        ]
        return lines


xx = {
  "id": "c09aafc994ea4829b6315da7939e7b1e",
  "directory": "ops/example",
  "name": "ben-example",
  "description": "",
  "isErr": False,
  "err": "",
  "plans": [
    {
      "id": "ctx",
      "name": "ben1",
      "isErr": False,
      "err": "",
      "unitGroups": [
        {
          "idx": 0,
          "seconds": 0,
          "times": 1000,
          "units": [
            {
              "name": "echohello",
              "parallel": 10,
              "limit": 0,
              "success": 990,
              "total": 990,
              "qps": 304.70342046517436,
              "code": {},
              "elapse": 31743496,
              "rate": 1.0,
              "resTime": 104178,
              "startTime": "2022-04-09T21:09:29.590872",
              "endTime": "2022-04-09T21:09:32.839933",
              "isErr": False,
              "err": ""
            }
          ]
        },
        {
          "idx": 1,
          "seconds": 2,
          "times": 0,
          "units": [
            {
              "name": "echohello",
              "parallel": 10,
              "limit": 0,
              "success": 624,
              "total": 624,
              "qps": 321.5424142270151,
              "code": {},
              "elapse": 18906149,
              "rate": 1.0,
              "resTime": 58798,
              "startTime": "2022-04-09T21:09:32.905648",
              "endTime": "2022-04-09T21:09:34.846294",
              "isErr": False,
              "err": ""
            }
          ]
        }
      ]
    }
  ]
}