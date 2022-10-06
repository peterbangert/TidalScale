
from config import config
from src.service.metric_consumer import MetricConsumer
from src.service.aggregate_prediction_retriever import PredictionRetriever
from src.service.flink_controller import FlinkController
import src.service.db_interface as db
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
        self.lag_history = []
        self.current_parallelism = 0
        self.cooldown_timestamp = datetime.utcnow() - timedelta(seconds=config.CONFIG['rescale_window'] - 20)
        self.agg_prediction = 0
        self.lag_recovery_mode = False

        #if not self.flink_controller.check_flink_deployment():
        #    self.flink_controller.deploy_flink()

    def run(self):

        while True:

            metric_report = self.consumer.get_next_message()
            if metric_report:
                logger.info("===============================================")
                logger.info(f"Recieved Metric Report")
                self.process_metrics(metric_report)
            else:
                time.sleep(1)

    def process_metrics(self, metric_report):

        try:
            ## Parse Metric Report
            cpu_usage = float(metric_report['cpuUsage'][0]['value'][1])
            taskmanagers = int(metric_report['flinkNumOfTaskManagers'][0]['value'][1])
            kafka_lag = float(metric_report['kafkaLag'][0]['value'][1])
            flink_ingestion = float(metric_report['flinkIngestionRate'][0]['value'][1])
            self.current_parallelism = taskmanagers if not math.isnan(taskmanagers) else self.current_parallelism

            timestamp, msg_per_second = 0, 0
            for item in metric_report['kafkaMessagesPerSecond']:
                if item['metric']['topic'] == "data":
                    msg_per_second = float(item['value'][1])
                    timestamp = datetime.strptime(metric_report['timestamp'], config.CONFIG['time_fmt'])
            mem_usage = float(metric_report['memUsage'][0]['value'][1])

            ## Return if Metrics a NaN
            if math.isnan(msg_per_second) or msg_per_second == '' or msg_per_second == 0:
                return 0
        except Exception as e:
            logger.info(f"Error parsing metrics, skipping.")
            logger.info(f"Stack Trace: {e}")
            return 0

        ### Update Lag Metrics
        std, median = self.update_lag_tracker(kafka_lag)


        ###
        #   Core Rescaling Logic
        ###
        rescale_bool, upscale = self.rescale_check(mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std)

        if rescale_bool:

            if datetime.utcnow() - timedelta(seconds=config.CONFIG['rescale_window']) < self.cooldown_timestamp:
                logger.info("Rescale Aborted: Within cooldown window")
            else:

                ## Get Target Parallelism
                target_parallelism = self.get_configuration()
                if target_parallelism is None:
                    target_parallelism = self.quotient_scale(flink_ingestion, msg_per_second)
                target_parallelism = self.scale_bounds(target_parallelism, upscale)

                ## Lag Recovery Mode
                if upscale and self.check_lag_recovery_mode(flink_ingestion, kafka_lag):
                    target_parallelism = self.get_lag_recovery_parallelism(flink_ingestion,kafka_lag,target_parallelism)

                ## Check if Target Parallelism is correct
                if (upscale and target_parallelism > self.current_parallelism)\
                        or (not upscale and target_parallelism < self.current_parallelism):
                    self.flink_controller.rescale(target_parallelism)
                    self.cooldown_timestamp = datetime.utcnow()
                else:
                    logger.info(f"Rescale Aborted: Target Parallelism incorrect. Upscale: {upscale}, Target: {target_parallelism}, current: {self.current_parallelism}")

    def get_lag_recovery_parallelism(self, flink_ingestion, kafka_lag, target_parallelism):
        workload = self.agg_prediction * config.CONFIG['rescale_window'] + kafka_lag
        t_ingestion_rate = math.ceil(workload / config.CONFIG['rescale_window'])
        t_parrallelism = math.ceil(( t_ingestion_rate / flink_ingestion ) * self.current_parallelism)
        if t_parrallelism < target_parallelism:
            logger.info(f"Lag Recovery Parallelism less than Regression Parallelism: t_p {t_parrallelism}, target {target_parallelism}")
            t_parrallelism = target_parallelism
        logger.info(f"Target Parallelism: {t_parrallelism}.  workload: {workload}, t_ingestion_rate: {t_ingestion_rate}, c_ingestion_rate: {flink_ingestion}")

        return t_parrallelism


    def check_lag_recovery_mode(self, flink_ingestion, kafka_lag):
        if self.agg_prediction == 0: return False

        workload = self.agg_prediction * config.CONFIG['rescale_window'] + kafka_lag
        ingestion_power = flink_ingestion * config.CONFIG['rescale_window']

        if workload > ingestion_power:
            logger.info("Lag Recovery Mode Detected")
            return True
        else:
            return False

    def scale_bounds(self, target_parallelism, upscale):
        if target_parallelism > config.CONFIG['parallelization_upper_bound']:
            logger.info(f"Rescale Target above appropriate Bounds. Target: {target_parallelism}")
            target_parallelism = config.CONFIG['parallelization_upper_bound']
        elif target_parallelism < config.CONFIG['parallelization_lower_bound']:
            logger.info(f"Rescale Target below appropriate Bounds. Target: {target_parallelism}")
            target_parallelism = config.CONFIG['parallelization_lower_bound']
        return target_parallelism

    def rescale_check(self, mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
        rescale_bool, upscale = False, False

        if self.overutilization_check(mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
            rescale_bool, upscale = True, True
            logger.info("Overutilizaiton Detected, Upscale Required")
        elif self.underutilization_check(mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
            rescale_bool, upscale = True, False
            logger.info("Underutilization Detected, Downscale Required")
        return rescale_bool, upscale

    def update_lag_tracker(self, kafka_lag):

        if math.isnan(kafka_lag):
            return 0, 0
        else:
            self.lag_history.append(int(kafka_lag))
        if len(self.lag_history) > config.CONFIG['rescale_window'] / config.CONFIG['metric_frequency']:
            self.lag_history.pop(0)
        lag_history_np = np.asarray(self.lag_history)
        std = lag_history_np.std()
        median = np.median(lag_history_np)

        #logger.info(f"Median: {median}, std {std}, lag: {kafka_lag}")
        return std, median

    def get_configuration(self):
        prediction = self.agg_prediction_retriever.get_prediction()
        self.agg_prediction = prediction['aggregate_prediction']
        target_config = db.get_configuration(self.agg_prediction)
        return target_config


    def quotient_scale(self, flink_ingestion, msg_per_second):
        return self.current_parallelism * math.ceil(msg_per_second/flink_ingestion)


    def underutilization_check(self, mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
        fail_criteria = False
        diagnosis = ""
        if  cpu_usage < config.THRESHOLDS['cpu_min'] \
                and kafka_lag < msg_per_second \
                and  mem_usage < config.THRESHOLDS['mem_max']:
            fail_criteria = True
            diagnosis += f"CPU Usage too Low: {cpu_usage} | "
            diagnosis += f"Lag lower than MSG/s: Lag: {kafka_lag}, msg/s: {msg_per_second} | "

        if diagnosis != "":
            logger.info(f"{diagnosis}")
        return fail_criteria


    def overutilization_check(self, mem_usage, cpu_usage, kafka_lag, msg_per_second, median, std):
        fail_criteria = False
        diagnosis = ""
        if mem_usage > config.THRESHOLDS['mem_max']:
            fail_criteria = True
            diagnosis += f"Memory Usage too High: {mem_usage} | "

        if config.THRESHOLDS['cpu_max'] < cpu_usage:
            fail_criteria = True
            diagnosis += f"CPU Usage too High/Low: {cpu_usage} | "

        if kafka_lag > msg_per_second:
            fail_criteria = True
            diagnosis += f"Lag Higher than MSG/s: Lag: {kafka_lag}, msg/s: {msg_per_second} | "

        #if abs(kafka_lag - median) > std * 2:
        #    fail_criteria = True
        #    diagnosis += f"Lag greater than 2 std deviations: lag-mean = {kafka_lag - median}, 2*std = {std * 2} | "

        if diagnosis != "":
            logger.info(f"{diagnosis}")
        return fail_criteria
