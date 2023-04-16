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



class LongTermPredictionModel:

    def __init__(self,args):
        logger.info("Initializing Short Term Prediction Model")
        self.trace_history = []
        self.prediction_model = TripleExponentialSmoothing()
        self.current_time = datetime.utcnow()
        self.time_fmt = config.config['time_fmt']        
        self.lt_horizon = 0
        self.lt_prediction = 0
        self.next_step_horizon = []
        self.next_step_prediction = []
        self.smape = 0
        

    def get_prediction(self):
        return self.lt_horizon, self.lt_prediction

    def get_next_step(self, timestamp):
        rtn_tmstp, rtn_prediction = 0,0
        if len(self.next_step_horizon) > 0:    
            for index, tmstp in enumerate(self.next_step_horizon):
                rtn_tmstp = self.next_step_horizon[index]
                rtn_prediction = self.next_step_prediction[index]
                if abs((tmstp - timestamp).total_seconds() ) < config.config['metric_frequency'] or tmstp > timestamp :
                    break
        return rtn_tmstp, rtn_prediction

    def calculate_smape(self, metric):
        _, next_step_prediction = self.get_next_step(metric.timestamp)
        new_smape = (abs(metric.msg_per_second - next_step_prediction)/ (abs(metric.msg_per_second)+abs(next_step_prediction))) * 100
        self.smape = (config.config['smape_alpha']) * new_smape + (1 - config.config['smape_alpha']) * self.smape
        return self.smape

    def get_smape(self):
        return self.smape

    def update_predictions(self, metric):
        msg_per_second = metric.msg_per_second
        msg_timestamp = metric.timestamp


        # Return if Offline Training Data
        if metric.offline_training: 
            logger.info("=====================================Offline LT Predictor")
            self.trace_history.append((msg_timestamp, msg_per_second))
            return

        # If trace history new
        if len(self.trace_history) == 0:
            self.trace_history.append((msg_timestamp, msg_per_second))

        # If New measurement is at least 'seconds_between_traces' different from last metric.
        #      - with error of 'metric_frequency'
        # Set current metric timestamp to exactly minute difference
        elif (msg_timestamp - self.trace_history[-1][0]).seconds > config.config['seconds_between_traces'] - config.config['metric_frequency']:


            self.trace_history.append((msg_timestamp,msg_per_second))

        elif self.lt_prediction != 0 and self.lt_horizon !=0:
            logger.info("Not enough time between metrics")
            return


        # Prune old Metrics
        while len(self.trace_history) > 0 and self.trace_history[0][0] < self.trace_history[-1][0] - timedelta(
                hours=config.config['trace_history_duration_hours']):
            self.trace_history.pop(0)


        # 2 Season Cycles must be present in data to predict model on
        if len(self.trace_history) < 24 * config.config['traces_per_hour'] * 2:
            logger.info("Not enough cycles for LT prediction")
            return


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
        predictions, horizons = self.prediction_model.create_prediction(pd_trace)

        # self.lt_horizon = datetime.strptime(horizons[-1], config.config['time_fmt'])
        self.lt_horizon = horizons[-1]
        self.lt_prediction = predictions[-1]

        # next_step_horizon = datetime.strptime(horizons[0], config.config['time_fmt'])
        next_step_horizon = horizons[0]
        next_step_prediction = predictions[0]

        # print("Prediction horizons and Predictions")
        # print(predictions)
        # print(horizons)
        # print("==================================")
        

        interp_timestamps = [ msg_timestamp + timedelta(seconds=x*config.config['metric_frequency']) for x in range(1, int((next_step_horizon - msg_timestamp).total_seconds() /config.config['metric_frequency']))]
        x_interp = [x for x in range(len(interp_timestamps))]
        y_interp = list(np.interp(x_interp, (0,len(x_interp)+1), (msg_per_second,next_step_prediction)))
        y_interp.append(next_step_prediction)
        interp_timestamps.append(next_step_horizon)


        self.next_step_horizon = interp_timestamps
        self.next_step_prediction = y_interp
        





