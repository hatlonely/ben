#!/usr/bin/env python3


from datetime import datetime


class Monitor:
    # 开始采集指标，如果来自于其他平台数据，这里可以不实现
    def collect(self):
        pass

    # 指标单位
    # 例如: {
    #   "CPU": "percent",
    #   "Mem": "byte",
    #   "Disk": "byte",
    #   "IOR": "times",
    #   "IOW": "times",
    #   "NetIOR": "bit",
    #   "NetIOW": "bit",
    # }
    def unit(self):
        pass

    # 返回 [start, end] 之间的的统计数据
    # 统计数据为 dict[list[dict[time, value]]]，
    # 内层 list 为指标的集合，由于不同的指标之间可能有不同的时间，引入外层 dict 以支持不同的时间序列
    # 其中 dict 为统计的指标
    #   time 为时间，iso8601 格式，其他字段为指标值
    #   例如：{
    #     "time": "2022-04-12T03:24:32.758001",
    #     "value": 91.5,
    #   }
    def stat(self, start: datetime, end: datetime):
        pass
