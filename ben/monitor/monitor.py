#!/usr/bin/env python3


class Monitor:
    # 开始采集指标，如果来自于其他平台数据，这里可以不实现
    def collect(self):
        pass

    # 指标
    # 例如: ["CPU", "Mem", "Disk", "IOR", "IOW"]
    def keys(self):
        pass

    # 返回 [start, end] 之间的的统计数据
    # 统计数据为字典格式，其中 time 为时间，iso8601 格式，其他字段为指标值
    # 例如：{
    #   "time": "2022-04-12T03:24:32.758001",
    #   "CPU": 91.5,
    #   "Mem": 7955.0078125,
    #   "Disk": 455.3299369812012,
    #   "IOR": 11299237,
    #   "IOW": 7127913
    # }
    def stat(self, start, end):
        pass
