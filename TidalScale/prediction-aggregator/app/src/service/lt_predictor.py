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
import json


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

        # If New measurement is at least 'seconds_between_traces' different from last metric.
        #      - with error of 'metric_frequency'
        # Set current metric timestamp to exactly minute difference
        elif (msg_timestamp - self.trace_history[-1][0]).seconds > config.config['seconds_between_traces'] - config.config['metric_frequency']:

            minute_diff = int((msg_timestamp - self.trace_history[-1][0]).seconds / config.config['seconds_between_traces'])
            minute_diff = 1 if minute_diff == 0 else minute_diff

            msg_timestamp = self.trace_history[-1][0] + timedelta(seconds=minute_diff * config.config['seconds_between_traces'])
            self.trace_history.append((msg_timestamp,msg_per_second))

        else:
            logger.info("Not enough time between metrics")
            return 0,0


        # Prune old Metrics
        while len(self.trace_history) > 0 and self.trace_history[0][0] < self.trace_history[-1][0] - timedelta(
                hours=config.config['trace_history_duration_hours']):
            self.trace_history.pop(0)


        # 2 Season Cycles must be present in data to predict model on
        if len(self.trace_history) < 24 * config.config['traces_per_hour'] * 2:
            logger.info("Not enough cycles for LT prediction")
            return 0,0

        # Return if Offline Training Data
        if offline: 
            logger.info("=====================================Offline LT Predictor")
            return 0,0

        ## Convert Trace History to Pandas DataFrame
        # 1. Create Series with timestamp as index
        timestamp_idx = [x[0] for x in self.trace_history]
        vals = [x[1] for x in self.trace_history]
        pd_trace = pd.Series(vals, index=timestamp_idx,name='load')

        # 2. Set a frequency to create missing timestamps
        pd_trace = pd_trace.asfreq(freq=f"{config.config['seconds_between_traces']}S")
        
        # 3. Interpolate to convert NaN values into interpolated values
        pd_trace.interpolate(inplace=True)

        # 4. Convert to DataFrame
        pd_trace = pd_trace.to_frame()

        # Get Prediction
        prediction, prediction_horizon = self.prediction_model.create_prediction(pd_trace)
        


        return prediction_horizon, prediction




