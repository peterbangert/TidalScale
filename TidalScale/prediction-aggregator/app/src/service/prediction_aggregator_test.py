from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from src.service.st_predictor import ShortTermPredictionModel
from src.service.lt_predictor import LongTermPredictionModel
from src.service.metric_consumer import MetricConsumer
from src.service.agg_prediction_producer import AggregatePredictionProducer
import time
import math
import numpy as np
from datetime import datetime, timedelta

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

class PredictionAggregator:

    def __init__(self,args):
        logger.info("Initializing Prediction Aggregator")
        self.synthetic_trace = args.synthetic
        self.timestamp = 0
        self.trace_history_lowgran = []
        self.trace_history_highgran = []
        self.st_history_lowgran = []
        self.st_history_highgran = [] 
        self.lt_history_lowgran = []
        self.lt_history_highgran = []
        self.lt_prediction = 0
        self.st_prediction = 0

        ## High/Low Gran Scores


        ## High/Low granularity Weights
        self.st_high_gran_linear_weight, self.lt_high_gran_linear_weight = 0,0
        self.st_high_gran_exp_weight, self.lt_high_gran_exp_weight = 0,0
        self.st_low_gran_linear_weight, self.lt_low_gran_linear_weight = 0,0
        self.st_low_gran_exp_weight, self.lt_low_gran_exp_weight = 0,0

        ## High/Low Gran Aggregate Predictions
        self.agg_high_gran_linear_prediction = 0
        self.agg_high_gran_exp_prediction = 0
        self.agg_low_gran_linear_prediction = 0
        self.agg_low_gran_exp_prediction = 0
        

    
    def update_prediction(self, prediction_data):


        timestamp = prediction_data['timestamp']
        self.timestamp = timestamp
        msg_per_second = prediction_data['msg_per_second']
        st_horizon = prediction_data['st_horizon']
        lt_horizon = prediction_data['lt_horizon']
        st_prediction = prediction_data['st_prediction']
        lt_prediction = prediction_data['lt_prediction']

        self.trace_history_highgran = self.append_and_prune(timestamp, msg_per_second, self.trace_history_highgran)

        # Update Low Granularity Histories
        if lt_prediction != 0:

            if st_prediction == 0:
                if len(self.st_history_lowgran) > 0:
                    st_prediction = self.st_history_lowgran[-1][1]
                    st_horizon = timestamp
            else:
                self.st_history_lowgran = self.append_and_prune(st_horizon, st_prediction, self.st_history_lowgran)

            self.trace_history_lowgran = self.append_and_prune(timestamp, msg_per_second, self.trace_history_lowgran)
            self.lt_history_lowgran = self.append_and_prune(lt_horizon, lt_prediction, self.lt_history_lowgran)

            # Update High Granularity LT History
            prev_timestamp = self.st_history_lowgran[-1][0]
            prev_prediction = self.st_history_lowgran[-1][1]

            # Interpolate between current and previous LT predictions
            interp_timestamps = [ prev_timestamp + timedelta(seconds=x*2) for x in range(int((timestamp - prev_timestamp).total_seconds() /2))]
            x_interp = [x for x in range(1, len(interp_timestamps))]
            y_interp = np.interp(x_interp, (0,len(x_interp)+1), (prev_prediction,lt_prediction))
            interp_predictions = list(zip(x_interp,y_interp))

            self.lt_history_highgran += interp_predictions
            self.lt_history_highgran = self.append_and_prune(lt_horizon, lt_prediction, self.lt_history_highgran)

        # Update High Granulatiry
        else:

            if len(self.lt_history_lowgran) > 0:
                lt_prediction = self.lt_history_lowgran[-1][1]
            else:
                lt_prediction = 0
                lt_score = 0

            if st_prediction == 0:
                if len(self.st_history_highgran) > 0:
                    st_prediction = self.st_history_highgran[-1][1]
                    st_horizon = timestamp
            else:
                self.st_history_highgran = self.append_and_prune(st_horizon, st_prediction, self.st_history_highgran)

        self.st_prediction = st_prediction
        self.lt_prediction = lt_prediction

        ## High Granularity Linear
        self.linear = True
        st_score, st_prediction = self.calculate_score(st_prediction, self.st_history_highgran, self.trace_history_highgran)
        lt_score, lt_prediction = self.calculate_score(lt_prediction, self.lt_history_highgran, self.trace_history_highgran)
        self.st_high_gran_linear_weight, self.lt_high_gran_linear_weight = self.calculate_weight(st_score, lt_score)
        self.agg_high_gran_linear_prediction = self.aggregate(self.st_high_gran_linear_weight, self.lt_high_gran_linear_weight, st_prediction, lt_prediction)

        ## High Granularity Exponential
        self.linear = False
        st_score, st_prediction = self.calculate_score(st_prediction, self.st_history_highgran, self.trace_history_highgran)
        lt_score, lt_prediction = self.calculate_score(lt_prediction, self.lt_history_highgran, self.trace_history_highgran)
        self.st_high_gran_exp_weight, self.lt_high_gran_exp_weight = self.calculate_weight(st_score, lt_score)
        self.agg_high_gran_exp_prediction = self.aggregate(self.st_high_gran_exp_weight, self.lt_high_gran_exp_weight, st_prediction, lt_prediction)

        ## Low Granularity Linear
        self.linear = True
        st_score, st_prediction = self.calculate_score(st_prediction, self.st_history_highgran, self.trace_history_lowgran)
        lt_score, lt_prediction = self.calculate_score(lt_prediction, self.lt_history_highgran, self.trace_history_lowgran)
        self.st_low_gran_linear_weight, self.lt_low_gran_linear_weight = self.calculate_weight(st_score, lt_score)
        self.agg_low_gran_linear_prediction = self.aggregate(self.st_low_gran_linear_weight, self.lt_low_gran_linear_weight, st_prediction, lt_prediction)

        ## Low Granulatiry Exponential
        self.linear = False
        st_score, st_prediction = self.calculate_score(st_prediction, self.st_history_highgran, self.trace_history_lowgran)
        lt_score, lt_prediction = self.calculate_score(lt_prediction, self.lt_history_highgran, self.trace_history_lowgran)
        self.st_low_gran_exp_weight, self.lt_low_gran_exp_weight = self.calculate_weight(st_score, lt_score)
        self.agg_low_gran_exp_prediction = self.aggregate(self.st_low_gran_exp_weight, self.lt_low_gran_exp_weight, st_prediction, lt_prediction)
        


    def aggregate(self, st_weight, lt_weight, st_prediction, lt_prediction):
        st_prediction_weighted = st_prediction * st_weight
        lt_prediction_weighted = lt_prediction * lt_weight

        ## Aggregate weighted Scores
        return st_prediction_weighted + lt_prediction_weighted
        

    def calculate_weight(self, st_score, lt_score):
        # Calculate Weighted Score
        ## Happens when no new LT prediction, and ST determined new data is outlier
        if st_score == 0 and lt_score ==0:
            logger.info("Returning, Likely no history for SMAPE to evaluate")
            return 0,0
        elif st_score == 0 or lt_score ==0:
            ## Calculate Weighted Scores
            st_weight = int(bool(st_score))
            lt_weight = int(bool(lt_score))
        else:
            ## Calculate Weighted Scores
            st_weight = 1 - (st_score / (st_score + lt_score))
            lt_weight = 1 - (lt_score / (st_score + lt_score))

        return st_weight, lt_weight


    def calculate_score(self, x_prediction, x_pred_history, real_history):
        if x_prediction != 0:
            x_score = self.get_smape_score(x_pred_history, real_history)

        else:
            if len(x_pred_history) > 0:
                x_prediction = x_pred_history[-1][1]
                x_score = self.get_smape_score(x_pred_history, real_history)
            else:
                x_prediction = 0
                x_score = 0
        return x_score, x_prediction
    

    def append_and_prune(self, timestamp, data, tuple_list):
        tuple_list.append((timestamp, data))
        while len(tuple_list) > 0 and tuple_list[0][0] < tuple_list[-1][0] - timedelta(
                seconds=config.config['rescale_window'] * 2):
            tuple_list.pop(0)
        return tuple_list



    '''
        Linearly Decaying SMAPE Score
        Symmetric Mean Absolute Percentage Error (SMAPE)
    '''
    def get_smape_score(self, predictions, real_history):

        utc_now = datetime.utcnow()
        utc_now = self.timestamp if self.synthetic_trace else datetime.utcnow()
        prediction_history = []

        for i in predictions:
            if i[0] < utc_now:
                prediction_history.append(i)

        if len(prediction_history) == 0:
            logger.info(f"GET SMAPE: No predition history")
            return 0

        if len(real_history) == 0:
            logger.info(f"GET SMAPE: No Trace History history")
            return 0

        trace_prediction_zip = []
        trace_idx = 0
        pred_idx = 0
        for i in range(len(real_history) + len(prediction_history)):

            trace = real_history[trace_idx]
            prediction = prediction_history[pred_idx]

            if abs(trace[0] - prediction[0]).total_seconds() <= config.config['metric_frequency']:
                trace_prediction_zip.append((trace[1], prediction[1]))
                trace_idx += 1
                pred_idx += 1
            elif trace < prediction:
                trace_idx += 1
            else:
                pred_idx +=1

            if trace_idx == len(real_history) or pred_idx == len(prediction_history):
                break

        if self.linear:
            smape = self.linear_decay_smape(trace_prediction_zip)
        else:
            smape = self.exponential_decay_smape(trace_prediction_zip)
        

        if smape == 0:
            logger.info("============")
            logger.info(f"PREDICTIONS: {predictions}")
            logger.info(f"TRACE HISTORY: {real_history}")
            logger.info("============")

        return smape


    def exponential_decay_smape(self,trace_prediction_zip):
        n = len(trace_prediction_zip)

        if n == 0:
            logger.info(f"GET SMAPE: Trace/Prediction zip length 0")
            return 0

        smape = 0
        for i in range(n):
            trace =trace_prediction_zip[i][0]
            pred = trace_prediction_zip[i][1]
            smape = (0.5) * smape + (0.5) * (abs(trace - pred)/ (abs(trace)+abs(pred)))

        return smape

    def linear_decay_smape(self, trace_prediction_zip):
        n = len(trace_prediction_zip)

        if n == 0:
            logger.info(f"GET SMAPE: Trace/Prediction zip length 0")
            return 0

        smape = 0
        for i in range(len(trace_prediction_zip)):
            trace =trace_prediction_zip[i][0]
            pred = trace_prediction_zip[i][1]
            smape += (1/(n-i+1)) * (abs(trace - pred)/ (abs(trace)+abs(pred)))

        smape = smape / n

        return smape
