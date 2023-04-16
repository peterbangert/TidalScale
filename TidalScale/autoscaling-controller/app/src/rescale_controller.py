
from config import config
from src.service.metric_consumer import MetricConsumer
from src.service.aggregate_prediction_retriever import PredictionRetriever
from src.service.flink_controller import FlinkController
import src.service.db_interface as db
from src.obj.metric import Metric
from src.obj.lag_tracker import LagTracker
import time
from datetime import datetime, timedelta
import json
import numpy as np
import math

import logging
logger = logging.getLogger(__name__)


class RescaleController:

    def __init__(self ,args):
        logger.info("Initializing Metric Reporter")
        self.args = args
        self.consumer = MetricConsumer(args)
        self.agg_prediction_retriever = PredictionRetriever(args)
        self.flink_controller = FlinkController(args)
        self.lag_tracker = LagTracker()
        self.cooldown_timestamp = datetime.utcnow() - timedelta(seconds=config.config['rescale_window'] - 20)
        self.upscale = False
        self.downscale = False


        #if not self.flink_controller.check_flink_deployment():
        #    self.flink_controller.deploy_flink()


    def run(self):

        # Main Logic Loop
        while True:
            metric_report = self.consumer.get_next_message()
            if metric_report:
                try:
                    logger.info(f"Recieved Metric Report")
                    metric = Metric(metric_report)
                    
                    self.lag_tracker.update_lag_tracker(metric)
                    self.rescale_check(metric)
                except Exception as e:
                    logger.error(f"{e}")
                    continue
            else:
                # Metrics are reported every 2 seconds
                time.sleep(1)


    def rescale_check(self, metric):

        self.upscale = False
        self.downscale = False

        if self.overutilization_check(metric) or self.underutilization_check(metric):

            if datetime.utcnow() - timedelta(seconds=config.config['rescale_window']) < self.cooldown_timestamp:
                logger.info("Rescale Aborted: Within cooldown window")
            else:

                
                ## Get Future Load Prediction
                try:
                    prediction = self.agg_prediction_retriever.get_prediction()
                    agg_prediction = prediction['aggregate_prediction']
                except Exception as e:
                    logger.info(f"Kafka Prediction Model Error: {e}")
                    agg_prediction = metric.msg_per_second

                ## Calculate Workload for next scaling window
                workload = ((agg_prediction + metric.msg_per_second) / 2) * config.config['rescale_window'] + metric.kafka_lag
                
                ## Get Target Ingestion Rate
                target_ingestion_rate = math.ceil(workload / config.config['rescale_window'])
                
                ## Get Target Parallelism
                target_parallelism = db.get_configuration(target_ingestion_rate)
                
                if target_parallelism is None:
                    target_parallelism = self.quotient_scale(target_ingestion_rate ,metric)
                target_parallelism = self.scale_bounds(target_parallelism)

                ## Lag Recovery Mode
                if self.upscale and self.lag_tracker.check_lag_recovery_mode(metric, agg_prediction):
                    target_parallelism = self.lag_tracker.get_lag_recovery_parallelism(metric, target_parallelism, agg_prediction)
                

                ## Check if Target Parallelism is correct
                if (self.upscale and target_parallelism > metric.taskmanagers) \
                        or (self.downscale and target_parallelism < metric.taskmanagers):
                    self.flink_controller.rescale(target_parallelism)
                    self.cooldown_timestamp = datetime.utcnow()
                else:
                    logger.info(f"Rescale Aborted: Target Parallelism incorrect. Upscale: {self.upscale}, Downscale: {self.downscale}, Target: {target_parallelism}, current: {metric.taskmanagers}")

        else:
            logger.info(f"No action")

    def scale_bounds(self, target_parallelism):
        if target_parallelism > config.config['parallelization_upper_bound']:
            logger.info(f"Rescale Target above appropriate Bounds. Target: {target_parallelism}")
            target_parallelism = config.config['parallelization_upper_bound']
        elif target_parallelism < config.config['parallelization_lower_bound']:
            logger.info(f"Rescale Target below appropriate Bounds. Target: {target_parallelism}")
            target_parallelism = config.config['parallelization_lower_bound']
        return target_parallelism


    def quotient_scale(self, target_ingestion_rate, metric):
        t_parallelism = math.ceil(metric.taskmanagers * target_ingestion_rate/metric.flink_ingestion)
        logger.info(f"Quotient Scale: target: {t_parallelism}, t_ingestion_rate: {target_ingestion_rate}, curr_ingestion_rate: {metric.flink_ingestion} ")
        return math.ceil(metric.taskmanagers * target_ingestion_rate/metric.flink_ingestion)


    def underutilization_check(self, metric):
        fail_criteria = False
        diagnosis = ""
        if  metric.cpu_usage < config.thresholds['cpu_min'] \
                and metric.kafka_lag < metric.msg_per_second \
                and  metric.mem_usage < config.thresholds['mem_max']:
            fail_criteria = True
            diagnosis += f"CPU Usage too Low: {metric.cpu_usage} | "
            diagnosis += f"Lag lower than MSG/s: Lag: {metric.kafka_lag}, msg/s: {metric.msg_per_second} | "

        if diagnosis != "":
            logger.info(f"{diagnosis}")

        self.downscale = fail_criteria
        
        return fail_criteria


    def overutilization_check(self, metric):
        fail_criteria = False
        diagnosis = ""
        if metric.mem_usage > config.thresholds['mem_max']:
            fail_criteria = True
            diagnosis += f"Memory Usage too High: {metric.mem_usage} | "

        if config.thresholds['cpu_max'] < metric.cpu_usage:
            fail_criteria = True
            diagnosis += f"CPU Usage too High/Low: {metric.cpu_usage} | "

        if metric.kafka_lag > metric.msg_per_second:
            fail_criteria = True
            diagnosis += f"Lag Higher than MSG/s: Lag: {metric.kafka_lag}, msg/s: {metric.msg_per_second} | "

        #if abs(kafka_lag - median) > std * 2:
        #    fail_criteria = True
        #    diagnosis += f"Lag greater than 2 std deviations: lag-mean = {kafka_lag - median}, 2*std = {std * 2} | "

        if diagnosis != "":
            logger.info(f"{diagnosis}")

        self.upscale = fail_criteria

        return fail_criteria
