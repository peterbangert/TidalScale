from config import config
from datetime import datetime, timedelta
from src.service.database import Database
import numpy as np
from statistics import mean

import logging
logger = logging.getLogger(__name__)


class ConfigurationManager:

    def __init__(self,args):
        self.database = Database(args)

    def update_configurations(self, metric):
        # New Approach is CPU agnosticy
        cpu_usage_rounded = round(metric.cpu_usage,1)

        # Criteria for saving metrics
        if cpu_usage_rounded > 1.0: 
            return 0

        max_rate, ema_rate = self.database.get_rates(metric.taskmanagers, cpu_usage_rounded)
        max_rate = self.database.check_max_rate(metric.taskmanagers, cpu_usage_rounded)
        
        if max_rate:

            ## Exponentnial Smoothing
            ema_rate = (config.config['alpha']) * metric.flink_ingestion + (1 - config.config['alpha']) * ema_rate

            if max_rate < metric.flink_ingestion:
                logger.info("-------------------")
                logger.info(f"Updating Max Rate and ema_rate for {metric.taskmanagers} at {cpu_usage_rounded}cpu to MAX:{metric.flink_ingestion}, ema:{ema_rate}")
                logger.info("-------------------")
                self.database.update_rates(
                    taskmanagers=metric.taskmanagers,
                    cpu=cpu_usage_rounded,
                    max_rate=metric.flink_ingestion,
                    ema_rate=ema_rate)
            else:
                self.database.update_ema_rate(
                    taskmanagers=metric.taskmanagers,
                    cpu=cpu_usage_rounded,
                    ema_rate=ema_rate)
                logger.info(f"Updating ema_rate for {metric.taskmanagers} at {cpu_usage_rounded}cpu to {ema_rate}")
        else:
            logger.info("-------------------")
            logger.info(f"Inserting New Entry: Parallelism {metric.taskmanagers} at {cpu_usage_rounded}cpu to {metric.flink_ingestion}")
            logger.info("-------------------")
            self.database.insert_rates(
                taskmanagers=metric.taskmanagers,
                cpu=cpu_usage_rounded,
                max_rate=metric.flink_ingestion,
                ema_rate=metric.flink_ingestion,
                parallelism=metric.taskmanagers)
