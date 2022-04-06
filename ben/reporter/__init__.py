#!/usr/bin/env python3


from .reporter import Reporter
from .text_repoter import TextReporter
from .json_repoter import JsonReporter
from .html_repoter import HtmlReporter


reporter_map = {
    "text": TextReporter,
    "json": JsonReporter,
    "html": HtmlReporter,
}


__all__ = [
    "Reporter",
    "TextReporter",
    "JsonReporter",
    "HtmlReporter",
    "reporter_map",
]
