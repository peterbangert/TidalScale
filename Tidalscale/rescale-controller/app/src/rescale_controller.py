
from config import config
from src.service.metric_consumer import MetricConsumer
from src.service.database import Database
import time
from datetime import datetime
import json
import numpy as np
import math

import logging
logger = logging.getLogger(__name__)


class PerformanceMeter:

    def __init__(self ,args):
        logger.info("Initializing Metric Reporter")
        self.args = args
        self.consumer = MetricConsumer(args)
        self.database = Database(args)
        self.lag_history = []

    def run(self):

        while True:

            metric_report = self.consumer.get_next_message()
            if metric_report:
                logger.info(f"Recieved Metric Report")
                self.process_metrics(metric_report)
            else:
                time.sleep(1)

    def process_metrics(self, metric_report):
        cpu_usage = float(metric_report['cpuUsage'][0]['value'][1])
        taskmanagers = int(metric_report['flinkNumOfTaskManagers'][0]['value'][1])
        kafka_lag = float(metric_report['kafkaLag'][0]['value'][1])

        std, median = 0, 0
        if math.isnan(kafka_lag):
            return 0
        else:
            self.lag_history.append(int(kafka_lag))
        if len(self.lag_history) > config.CONFIG['rescale_window'] / config.CONFIG['metric_frequency']:
            self.lag_history.pop(0)
            lag_history_np = np.asarray(self.lag_history)
            std = lag_history_np.std()
            median = np.median(lag_history_np)

        logger.info(f"Median: {median}, std {std}, lag: {kafka_lag}")

        msg_per_second = 0
        for item in metric_report['kafkaMessagesPerSecond']:
            if item['metric']['topic'] == "data":
                msg_per_second = float(item['value'][1])
        mem_usage = float(metric_report['memUsage'][0]['value'][1])

        if self.pass_criteria(mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
            max_rate = self.database.check_max_rate(taskmanagers)
            if max_rate:
                if max_rate < msg_per_second:
                    logger.info(f"Updating Max Rate: Parallelism {taskmanagers} to {msg_per_second}")
                    self.database.update_performance(
                        id=taskmanagers,
                        max_rate=msg_per_second)
                else:
                    logger.info(f"Max Rate above current msg/s, Max Rate: {max_rate}, msg/s: {msg_per_second}")
            else:
                logger.info(f"Inserting New Entry: Parallelism {taskmanagers} at {msg_per_second}")
                self.database.insert_performance(
                    id=taskmanagers,
                    num_taskmanager_pods=taskmanagers,
                    max_rate=msg_per_second,
                    parallelism=taskmanagers)

    def pass_criteria(self, mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
        pass_criteria = True
        diagnosis = ""
        if mem_usage > config.THRESHOLDS['mem_max']:
            pass_criteria = False
            diagnosis += f"Memory Usage too High: {mem_usage} | "

        if config.THRESHOLDS['cpu_max'] < cpu_usage or cpu_usage < config.THRESHOLDS['cpu_min']:
            pass_criteria = False
            diagnosis += f"CPU Usage too High/Low: {cpu_usage} | "

        if kafka_lag > msg_per_second:
            pass_criteria = False
            diagnosis += f"Lag Higher than MSG/s: Lag: {kafka_lag}, msg/s: {msg_per_second} | "

        if abs(kafka_lag - median) > std * 2:
            pass_criteria = False
            diagnosis += f"Lag greater than 2 std deviations: lag-mean = {kafka_lag - median}, 2*std = {std * 2} | "

        if diagnosis != "":
            logger.info(f"{diagnosis}")

        return pass_criteria
