#!/usr/bin/env python3


import json
import locale
from types import SimpleNamespace


from ..util import merge


i18n = {
    "dft": {
        "title": {
            "test": "TEST",
            "plan": "PLAN",
            "unit": "UNIT",
            "step": "STEP",
        },
    },
    "en": {},
    "zh": {
        "title": {
            "test": "测试",
            "plan": "计划",
            "unit": "单元",
            "step": "步骤",
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
