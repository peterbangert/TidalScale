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
        self.st_horizon = 0
        self.st_prediction = 0
        self.next_step_horizon = 0
        self.next_step_prediction = 0
        self.smape = 0

    def get_prediction(self):
        return self.st_horizon, self.st_prediction

    def get_next_step(self):
        return self.next_step_horizon, self.next_step_prediction
    
    def calculate_smape(self, metric):
        _, next_step_prediction = self.get_next_step()
        new_smape = (abs(metric.msg_per_second - next_step_prediction)/ (abs(metric.msg_per_second)+abs(next_step_prediction))) *100
        self.smape = (config.config['smape_alpha']) * new_smape + (1 - config.config['smape_alpha']) * self.smape
        return self.smape

    def get_smape(self):
        return self.smape


    def update_predictions(self, metric):

        # Add to Trace History
        self.trace_history.append((metric.timestamp,metric.msg_per_second))
        while len(self.trace_history) >0 and self.trace_history[0][0] < metric.timestamp - timedelta(seconds=config.config['rescale_window'] *3):
            self.trace_history.pop(0)



        if len(self.trace_history) < config.config['base_regression_length']:
            logger.info("Not enough data for regression")
            self.horizon = 0
            self.predition = 0
            self.next_step_horizon = 0
            self.next_step_prediction = 0
            return

        # Calculate Regressions
        y = [x[1] for x in self.trace_history]
        x = np.array([*range(len(self.trace_history))])
        self.quadratic_regression = np.polyfit(x, y, 2)
        self.linear_regression = np.polyfit(x, y, 1)


        # Calculate future x for prediction
        future_x = len(self.trace_history) + (config.config['rescale_window'] / config.config['metric_frequency'])

        # Next step X value
        future_x_next_step = len(self.trace_history) + 1

        # future_x = 1
        # future_x_next_step =1

        # Calculate prediction based on Slope of data
        #if self.linear_regression[0] < 0:
        if self.quadratic_regression[0] > 0 and False:
            st_prediction = self.quadratic_regression[0] * future_x ** 2 + \
                         self.quadratic_regression[1] * future_x + \
                         self.quadratic_regression[2]
            next_step_prediction = self.quadratic_regression[0] * future_x_next_step ** 2 + \
                         self.quadratic_regression[1] * future_x_next_step + \
                         self.quadratic_regression[2]
        else:
            st_prediction = self.linear_regression[0] * future_x + \
                         self.linear_regression[1]
            next_step_prediction = self.linear_regression[0] * future_x_next_step + \
                         self.linear_regression[1]

        st_horizon = metric.timestamp + timedelta(seconds=config.config['rescale_window'])
        next_step_horizon = metric.timestamp + timedelta(seconds=config.config['metric_frequency'])

        # Set Value for later retrieval
        self.st_horizon = st_horizon
        self.st_prediction = st_prediction
        self.next_step_horizon = next_step_horizon
        self.next_step_prediction = next_step_prediction
        

