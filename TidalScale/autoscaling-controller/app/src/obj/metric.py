import math
from datetime import datetime, timedelta
from config import config

import logging
logger = logging.getLogger(__name__)


class Metric:

    def __init__(self,metric_report):

        # Check for Missing Data
        for x in ['cpuUsage','flinkNumOfTaskManagers','kafkaLag','memUsage','flinkIngestionRate']:
            if not bool(metric_report[x]):
                raise Exception('Metric Report Error: missing data')

            
        ## Parse Metric Report
        self.cpu_usage = float(metric_report['cpuUsage'][0]['value'][1])
        self.taskmanagers = int(metric_report['flinkNumOfTaskManagers'][0]['value'][1])
        self.kafka_lag = float(metric_report['kafkaLag'][0]['value'][1])
        self.flink_ingestion = float(metric_report['flinkIngestionRate'][0]['value'][1])
        self.mem_usage = float(metric_report['memUsage'][0]['value'][1])
        

        self.timestamp, self.msg_per_second = 0, 0
        for item in metric_report['kafkaMessagesPerSecond']:
            if item['metric']['topic'] == "data":
                self.msg_per_second = float(item['value'][1])
                self.timestamp = datetime.strptime(metric_report['timestamp'], config.config['time_fmt'])

        # Check for Nulls
        for x in [self.cpu_usage,self.taskmanagers,self.kafka_lag,self.msg_per_second,self.mem_usage,self.flink_ingestion]:
            if math.isnan(x) or x == '':
                raise Exception('Metric Report Error: null values')
