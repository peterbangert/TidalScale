
from config import config
from src.service.metric_consumer import MetricConsumer
from src.service.database import Database
import time
from datetime import datetime
import json
import numpy as np
import math
from statistics import mean

import logging
logger = logging.getLogger(__name__)


class PerformanceMeter:

    def __init__(self ,args):
        logger.info("Initializing Metric Reporter")
        self.args = args
        self.consumer = MetricConsumer(args)
        self.database = Database(args)
        self.lag_history = []
        self.flink_ingestion_smoothed = []
        self.cpu_smoothed = []
        self.mem_smoothed = []

    def run(self):

        # Main Logic Loop
        while True:
            metric_report = self.consumer.get_next_message()
            if metric_report:
                logger.info(f"Recieved Metric Report")
                self.process_metrics(metric_report)
            else:
                # Metrics are reported every 2 seconds
                time.sleep(1)

    def process_metrics(self, metric_report):

        for x in ['cpuUsage','flinkNumOfTaskManagers','kafkaLag','memUsage','flinkIngestionRate']:
            if not bool(metric_report[x]):
                logger.info("No data")
                return 0

        # Gather Metrics
        cpu_usage = float(metric_report['cpuUsage'][0]['value'][1])
        taskmanagers = int(metric_report['flinkNumOfTaskManagers'][0]['value'][1])
        kafka_lag = float(metric_report['kafkaLag'][0]['value'][1])
        mem_usage = float(metric_report['memUsage'][0]['value'][1])
        flink_ingestion = float(metric_report['flinkIngestionRate'][0]['value'][1])

        msg_per_second = 0
        for item in metric_report['kafkaMessagesPerSecond']:
            if item['metric']['topic'] == "data":
                msg_per_second = float(item['value'][1])

        # Check for Nulls
        for x in [cpu_usage,taskmanagers,kafka_lag,msg_per_second,mem_usage,flink_ingestion]:
            if math.isnan(x) or x == '':
                return 0

        # Get smoothed Flink Ingestion
        self.flink_ingestion_smoothed.append(flink_ingestion)
        if len(self.flink_ingestion_smoothed) > 5:
            self.flink_ingestion_smoothed.pop(0)

        # Get smoothed CPU Usage
        self.cpu_smoothed.append(cpu_usage)
        if len(self.cpu_smoothed) > 5:
            self.cpu_smoothed.pop(0)

        # Get smoothed Memory Usage
        self.mem_smoothed.append(mem_usage)
        if len(self.mem_smoothed) > 5:
            self.mem_smoothed.pop(0)

        # Kafka Lag History
        std, median = 0, 0
        self.lag_history.append(int(kafka_lag))
        if len(self.lag_history) > config.CONFIG['rescale_window'] / config.CONFIG['metric_frequency']:
            self.lag_history.pop(0)
            lag_history_np = np.asarray(self.lag_history)
            std = lag_history_np.std()
            median = np.median(lag_history_np)

        logger.info(f"Median: {median}, std {std}, lag: {kafka_lag}")


        if self.pass_criteria(mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
            max_rate = self.database.check_max_rate(taskmanagers)
            if max_rate:
                if max_rate < mean(self.flink_ingestion_smoothed):
                    logger.info("-------------------")
                    logger.info(f"Updating Max Rate: Parallelism {taskmanagers} to {mean(self.flink_ingestion_smoothed)}")
                    logger.info("-------------------")
                    self.database.update_performance(
                        id=taskmanagers,
                        max_rate=mean(self.flink_ingestion_smoothed))
                else:
                    logger.info(f"Max Rate above current msg/s, Max Rate: {max_rate}, msg/s: {msg_per_second}")
            else:
                logger.info("-------------------")
                logger.info(f"Inserting New Entry: Parallelism {taskmanagers} at {mean(self.flink_ingestion_smoothed)}")
                logger.info("-------------------")
                self.database.insert_performance(
                    id=taskmanagers,
                    num_taskmanager_pods=taskmanagers,
                    max_rate=mean(self.flink_ingestion_smoothed),
                    parallelism=taskmanagers)

    def pass_criteria(self, mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
        pass_criteria = True
        diagnosis = ""
        if mean(self.mem_smoothed) > config.THRESHOLDS['mem_max']:
            pass_criteria = False
            diagnosis += f"Memory Usage too High: {mem_usage} | "

        if config.THRESHOLDS['cpu_max'] < mean(self.cpu_smoothed) or mean(self.cpu_smoothed) < config.THRESHOLDS['cpu_min']:
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
