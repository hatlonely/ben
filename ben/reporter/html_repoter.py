#!/usr/bin/env python3


from .reporter import Reporter
from ..result import TestResult


class HtmlReporter(Reporter):
    def report(self, res: TestResult) -> str:
        return "html"
