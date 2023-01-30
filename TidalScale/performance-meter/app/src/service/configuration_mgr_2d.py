from config.config import config
from datetime import datetime, timedelta
from src.service.database import Database
import numpy as np
from statistics import mean

import logging
logger = logging.getLogger(__name__)


class ConfigurationManagerTwoDimensional:

    def __init__(self,args):
        self.database = Database(args)
        self.flink_ingestion_smoothed = []
        self.cpu_smoothed = []
        self.mem_smoothed = []
        self.lag_history = []
        self.cooldown_timer = datetime.now() - timedelta(seconds=30)



    def update_configurations(self, metric):

        # Smooth Metrics
        median, std = self.smooth_metrics(metric)
        flink_ingestion = mean(self.flink_ingestion_smoothed)



        if self.pass_criteria(metric, median, std):
        
            max_rate = self.database.check_max_rate(metric.taskmanagers, metric.cpu_usage)
            if max_rate:
                if max_rate < flink_ingestion:
                    logger.info("-------------------")
                    logger.info(f"Updating Max Rate: Parallelism {metric.taskmanagers} to {flink_ingestion}")
                    logger.info("-------------------")
                    self.database.update_performance(
                        taskmanagers=metric.taskmanagers,
                        cpu=metric.cpu_usage,
                        max_rate=flink_ingestion)
                else:
                    logger.info(f"Max Rate above current msg/s, Max Rate: {max_rate}, msg/s: {metric.msg_per_second}")
            else:
                logger.info("-------------------")
                logger.info(f"Inserting New Entry: Parallelism {metric.taskmanagers} at {flink_ingestion}")
                logger.info("-------------------")
                self.database.insert_performance(
                    taskmanagers=metric.taskmanagers,
                    cpu=metric.cpu_usage,
                    max_rate=flink_ingestion,
                    parallelism=metric.taskmanagers)


    def smooth_metrics(self, metric):

        # Get smoothed Flink Ingestion
        self.flink_ingestion_smoothed.append(metric.flink_ingestion)
        if len(self.flink_ingestion_smoothed) > 5:
            self.flink_ingestion_smoothed.pop(0)

        # Get smoothed CPU Usage
        self.cpu_smoothed.append(metric.cpu_usage)
        if len(self.cpu_smoothed) > 5:
            self.cpu_smoothed.pop(0)

        # Get smoothed Memory Usage
        self.mem_smoothed.append(metric.mem_usage)
        if len(self.mem_smoothed) > 5:
            self.mem_smoothed.pop(0)

        # Kafka Lag History
        std, median = 0, 0
        self.lag_history.append(int(metric.kafka_lag))
        if len(self.lag_history) > config.config['rescale_window'] / config.config['metric_frequency']:
            self.lag_history.pop(0)
            lag_history_np = np.asarray(self.lag_history)
            std = lag_history_np.std()
            median = np.median(lag_history_np)

        logger.info(f"Median: {median}, std {std}, lag: {metric.kafka_lag}")
        return median, std

    def pass_criteria(self, metric, median, std):
        pass_criteria = True
        diagnosis = ""
        if mean(self.mem_smoothed) > config.thresholds['mem_max']:
            pass_criteria = False
            diagnosis += f"Memory Usage too High: {metric.mem_usage} | "
        
        if config.thresholds['cpu_max'] < mean(self.cpu_smoothed) or mean(self.cpu_smoothed) < config.thresholds['cpu_min']:
            pass_criteria = False
            diagnosis += f"CPU Usage too High/Low: {metric.cpu_usage} | "

        if metric.kafka_lag > metric.msg_per_second:
            pass_criteria = False
            diagnosis += f"Lag Higher than MSG/s: Lag: {metric.kafka_lag}, msg/s: {metric.msg_per_second} | "

        if abs(metric.kafka_lag - median) > std * 2:
            pass_criteria = False
            diagnosis += f"Lag greater than 2 std deviations: lag-mean = {metric.kafka_lag - median}, 2*std = {std * 2} | "

        if diagnosis != "":
            logger.info(f"{diagnosis}")

        return pass_criteria
