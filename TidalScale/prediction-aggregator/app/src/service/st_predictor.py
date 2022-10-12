from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
import time
import math
import uuid
from datetime import datetime, timedelta
import numpy as np

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


class ShortTermPredictionModel:

    def __init__(self,args):
        logger.info("Initializing Short Term Prediction Model")
        self.trace_history = []
        self.spike_data = []
        self.linear_regression = []
        self.quadratic_regression = []
        self.MSE = 0




    def get_prediction(self, msg_timestamp, msg_per_second):


        ## SPIKE DETECTION
        ## Check if <8x MSE of Quadratic Regression
        if len(self.trace_history) > config.CONFIG['base_regression_length']:

            # Get Prediction for curtime, Current Time
            curr_prediction = self.linear_regression[0] * (len(self.trace_history)) + \
                              self.linear_regression[1]

            # Compare with current metric to see if outside MSE bounds
            if np.square(curr_prediction - msg_per_second) > config.CONFIG['MSE_bounds'] * self.MSE:
                self.spike_data.append((msg_timestamp, msg_per_second))
                if len(self.spike_data) > config.CONFIG['spike_window']:
                    logging.warning('Spike Detected')
                    self.trace_history = self.spike_data
                    self.spike_data = []
                else:
                    return 0, 0
            else:
                self.spike_data = []


        # Add to Trace History
        self.trace_history.append((msg_timestamp,msg_per_second))
        while len(self.trace_history) >0 and self.trace_history[0][0] < self.trace_history[-1][0] - timedelta(seconds=config.CONFIG['rescale_window'] *5):
            self.trace_history.pop(0)



        if len(self.trace_history) < config.CONFIG['base_regression_length']:
            logger.info("Not enough data for regression")
            return 0, 0

        # Calculate Regressions
        y = [x[1] for x in self.trace_history]
        x = np.array([*range(len(self.trace_history))])
        self.quadratic_regression = np.polyfit(x, y, 2)
        self.linear_regression = np.polyfit(x, y, 1)

        # Calculate future x for prediction
        future_x = (config.CONFIG['rescale_window'] / config.CONFIG['metric_frequency'])

        # Calculate MSE for spike detection
        self.MSE = np.square(np.subtract(y, np.polyval(self.linear_regression, x))).mean()

        # Calculate prediction based on Curve of data
        if self.quadratic_regression[0] > 0:
            prediction = self.quadratic_regression[0] * future_x ** 2 + \
                         self.quadratic_regression[1] * future_x + \
                         self.quadratic_regression[2]
        else:
            prediction = self.linear_regression[0] * future_x + \
                         self.linear_regression[1]

        timestamp = msg_timestamp + timedelta(seconds=config.CONFIG['rescale_window'])

        if msg_timestamp < datetime.utcnow() - timedelta(seconds=config.CONFIG['rescale_window']* 2):
            return 0,0

        return timestamp, prediction

