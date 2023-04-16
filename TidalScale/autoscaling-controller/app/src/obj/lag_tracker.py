from config import config
import src.service.db_interface as db
from datetime import datetime, timedelta
import math
import numpy as np

import logging
logger = logging.getLogger(__name__)


class LagTracker:

    def __init__(self):
        self.lag_counter = 0
        self.lag_history = []
        #self.std = 0
        #self.median = 0

    def check_lag_recovery_mode(self, metric, agg_prediction):
        if agg_prediction == 0: return False

        #workload = agg_prediction * config.config['rescale_window'] + metric.kafka_lag
        #ingestion_power = metric.flink_ingestion * config.config['rescale_window']

        if self.lag_history[-1] < metric.kafka_lag:
            self.lag_counter +=1
        else:
            self.lag_counter =0 

        return self.lag_counter >= 10
            

    def update_lag_tracker(self, metric):

        self.lag_history.append(int(metric.kafka_lag))
        if len(self.lag_history) > config.config['rescale_window'] / config.config['metric_frequency']:
            self.lag_history.pop(0)
        #lag_history_np = np.asarray(self.lag_history)
        #self.std = lag_history_np.std()
        #self.median = np.median(lag_history_np)


    def get_lag_recovery_parallelism(self, metric, target_parallelism, agg_prediction):
        logger.info(f"RESCALING: Lag Increasing on current parallelism. Prediction models too optimistic. {metric.taskmanagers +1}")
        self.lag_counter = 0

        ## Calculate Workload for next scaling window
        workload = ((agg_prediction + metric.msg_per_second) / 2) * config.config['rescale_window'] + metric.kafka_lag
        
        ## Get Target Ingestion Rate
        t_ingestion_rate = math.ceil(workload / config.config['rescale_window'])
        
        # Quotient Scale and Bound the Proposed rescale
        t_parrallelism = self.quotient_scale(metric.flink_ingestion, t_ingestion_rate)
        t_parrallelism = self.scale_bounds(t_parrallelism)
        
        # Check if Proposal is worse than Prediction Model proposal
        if t_parrallelism < target_parallelism:
            logger.info(f"Lag Recovery Parallelism less than Regression Parallelism: t_p {t_parrallelism}, target {target_parallelism}")
            t_parrallelism = target_parallelism
        logger.info(f"Target Parallelism: {t_parrallelism}.  workload: {workload}, t_ingestion_rate: {t_ingestion_rate}, c_ingestion_rate: {metric.flink_ingestion}")

        t_parrallelism = min(target_parallelism * 2, t_parrallelism)

        return t_parrallelism

    def scale_bounds(self, target_parallelism):
        if target_parallelism > config.config['parallelization_upper_bound']:
            logger.info(f"Rescale Target above appropriate Bounds. Target: {target_parallelism}")
            target_parallelism = config.config['parallelization_upper_bound']
        elif target_parallelism < config.config['parallelization_lower_bound']:
            logger.info(f"Rescale Target below appropriate Bounds. Target: {target_parallelism}")
            target_parallelism = config.config['parallelization_lower_bound']
        return target_parallelism


    def quotient_scale(self, target_ingestion_rate, metric):
        return math.ceil(metric.taskmanagers * target_ingestion_rate/metric.flink_ingestion)

