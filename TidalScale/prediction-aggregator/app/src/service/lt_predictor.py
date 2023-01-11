from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from src.service.tes import TripleExponentialSmoothing
import time
import math
import uuid
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


import logging
logger = logging.getLogger(__name__)

'''
Outgoing Data, 'st_prediction' topic example message:
{
    "occurredOn": timestamp of last observation
    "predictedWorkload":prediction
    "eventTriggerUuid": uuid of the last observation
    "eventType":"PredictionReported",
    "predictionBasedOnDateTime": timestamp of the predicted workload
    'uuid': event uuid           
}
'''


class LongTermPredictionModel:

    def __init__(self,args):
        logger.info("Initializing Short Term Prediction Model")
        self.trace_history = []
        self.prediction_model = TripleExponentialSmoothing()
        self.current_time = datetime.utcnow()
        self.time_fmt = config.config['time_fmt']


    def get_prediction(self, msg_timestamp, msg_per_second, offline):



        # If trace history new
        if len(self.trace_history) == 0:
            self.trace_history.append((msg_timestamp, msg_per_second))

        # If New measurement is at least 'time_interval' different from last metric.
        #      - with error of 'metric_frequency'
        # Set current metric timestamp to exactly minute difference
        elif (msg_timestamp - self.trace_history[-1][0]).seconds > config.config['time_interval'] - config.config['metric_frequency']:

            minute_diff = int((msg_timestamp - self.trace_history[-1][0]).seconds / config.config['time_interval'])
            minute_diff = 1 if minute_diff == 0 else minute_diff

            msg_timestamp = self.trace_history[-1][0] + timedelta(seconds=minute_diff * config.config['time_interval'])
            self.trace_history.append((msg_timestamp,msg_per_second))

        else:
            logger.info("Not enough time between metrics")
            return 0,0


        # Prune old Metrics
        #while len(self.trace_history) > 0 and self.trace_history[0][0] < datetime.utcnow() - timedelta(
        #        hours=config.config['trace_history_duration_hours']):
        #    self.trace_history.pop(0)


        # 2 Season Cycles must be present in data to predict model on
        if len(self.trace_history) < 24 * config.config['traces_per_hour'] * 2:
            logger.info("Not enough cycles for LT prediction")
            return 0,0

        # Return if Offline Training Data
        if offline: 
            logger.info("=====================================Offline LT Predictor")
            return 0,0

        # Dont create prediction if last measurement too old
        #if msg_timestamp < datetime.utcnow() - timedelta(seconds=config.config['rescale_window']* 2):
        #    return 0,0

        pd_trace = pd.DataFrame(self.trace_history, columns=['date','load'])
        pd_trace.set_index('date',inplace=True)

        # Get Prediction
        prediction, prediction_horizon = self.prediction_model.create_prediction(pd_trace)

        return prediction_horizon, prediction




