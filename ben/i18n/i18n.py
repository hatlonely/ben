#!/usr/bin/env python3


import json
import locale
from types import SimpleNamespace


from ..util import merge


i18n = {
    "dft": {
        "title": {
            "test": "Test",
            "plan": "Plan",
            "unitGroup": "Unit Group",
            "unit": "Unit",
            "step": "Step",
            "err": "Err",
            "idx": "Index",
            "seconds": "Seconds",
            "times": "Times",
            "parallel": "Parallel",
            "limit": "Limit",
            "success": "Success",
            "total": "Total",
            "elapse": "Elapse",
            "rate": "Rate",
            "resTime": "ResTime",
            "qps": "QPS",
            "code": "Code",
            "summary": "Summary",
            "quantile": "Quantile",
            "quantileShort": "Q",
            "monitor": "Monitor",
        },
        "status": {
            "fail": "FAIL",
            "succ": "SUCCESS",
        },
        "tooltip": {
            "save": "Save",
        }
    },
    "en": {},
    "zh": {
        "title": {
            "test": "测试",
            "plan": "计划",
            "unitGroup": "单元组",
            "unit": "单元",
            "step": "步骤",
            "err": "错误",
            "idx": "序列",
            "seconds": "测试时间",
            "times": "测试次数",
            "parallel": "并发",
            "limit": "限流",
            "success": "成功",
            "total": "总共",
            "elapse": "耗时",
            "rate": "成功率",
            "resTime": "响应时间",
            "qps": "QPS",
            "code": "错误码",
            "summary": "汇总",
            "quantile": "分位数",
            "quantileShort": "Q",
            "monitor": "监测",
        },
        "status": {
            "fail": "失败",
            "succ": "成功",
        },
        "tooltip": {
            "save": "保存",
        }
    }
}


class I18n:
    def __init__(self, args=None):
        lang = "dft"
        try:
            lang = locale.getdefaultlocale()[0].split('_')[0]
        except Exception as e:
            pass

        if args is None:
            args = {}
        args = merge(args, {
            "lang": lang,
            "i18n": {},
        })

        lang = args["lang"]
        if lang not in i18n:
            lang = "dft"

        self.i18n_ = json.loads(
            json.dumps(merge(args["i18n"], merge(i18n[lang], i18n["dft"]))),
            object_hook=lambda x: SimpleNamespace(**x)
        )

    def i18n(self):
        return self.i18n_
