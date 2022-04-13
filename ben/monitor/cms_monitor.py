#!/usr/bin/env python3
import json
from datetime import timedelta, datetime
from typing import List
from alibabacloud_cms_export20211101.client import Client as cms_export20211101Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_cms_export20211101 import models as cms_export_20211101_models

from .monitor import Monitor
from ..util import merge, REQUIRED


# 支持的指标参考: <https://help.aliyun.com/document_detail/163515.html>
class CMSMonitor(Monitor):
    def __init__(self, args=None):
        args = merge(args, {
            "AccessKeyId": REQUIRED,
            "AccessKeySecret": REQUIRED,
            "InstanceId": REQUIRED,
            "RegionId": "",
            "Endpoint": "",
            "Metrics": REQUIRED,
            "Period": 60,
            "Namespace": "acs_ecs_dashboard",
        })
        config = open_api_models.Config(
            access_key_id=args["AccessKeyId"],
            access_key_secret=args["AccessKeySecret"],
        )
        if args["RegionId"]:
            config.endpoint = "cms-export.{}.aliyuncs.com".format(args["RegionId"])
        if args["Endpoint"]:
            config.endpoint = args["Endpoint"]

        self.client = cms_export20211101Client(config)
        self.period = 60
        self.instance_id = args["InstanceId"]
        self.namespace = args["Namespace"]
        self.metrics = []
        for m in args["Metrics"]:
            self.metrics.append(merge(m, {
                "Unit": "",
            }))

    def unit(self):
        return dict([(i["Name"], i["Unit"]) for i in self.metrics])

    def stat(self, start: datetime, end: datetime):
        metrics = {}
        for metric in self.metrics:
            req = cms_export_20211101_models.CursorRequest()
            req.namespace = self.namespace
            req.period = self.period
            req.metric = metric["Name"]
            req.start_time = int(start.timestamp()*1000)
            req.end_time = int(end.timestamp()*1000)
            req.matchers = json.dumps([{
                "instanceId": self.instance_id,
            }])
            req.matchers = [
                cms_export_20211101_models.CursorRequestMatchers(
                    label="instanceId",
                    value=self.instance_id,
                )
            ]
            res = self.client.cursor(req)
            if res.body.code != 200:
                return {
                    "err": res.body.message
                }
            req = cms_export_20211101_models.BatchGetRequest()
            req.namespace = self.namespace
            req.metric = metric["Name"]
            req.cursor = res.body.data.cursor
            req.length = 10000
            res = self.client.batch_get(req)
            if res.body.code != 200:
                return {
                    "err": res.body.message
                }
            measures = []
            for record in res.body.data.records:
                kvs = {}
                for idx in range(len(record.measure_labels)):
                    kvs[record.measure_labels[idx]] = record.measure_values[idx]
                measures.append({
                    "time": datetime.fromtimestamp(record.timestamp / 1000).isoformat(),
                    "value": float(kvs[metric["Statistic"]])
                })
            metrics[metric["Name"]] = measures
        return metrics
