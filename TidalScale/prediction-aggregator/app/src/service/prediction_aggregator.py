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
        self.st_future_predictions = []
        self.lt_future_predictions = []
        self.lt_prediction, self.st_prediction = 0,0
        self.st_weight, self.lt_weight = 0,0
        self.st_score, self.lt_score = 0,0
        self.agg_prediction = 0
        

    
    def update_prediction(self, prediction_data):


        timestamp = prediction_data['timestamp']
        self.timestamp = timestamp
        msg_per_second = prediction_data['msg_per_second']
        st_horizon = prediction_data['st_horizon']
        lt_horizon = prediction_data['lt_horizon']
        st_prediction = prediction_data['st_prediction']
        lt_prediction = prediction_data['lt_prediction']
        self.st_smape = prediction_data['st_smape']
        self.lt_smape = prediction_data['lt_smape']

        self.st_prediction = st_prediction
        self.lt_prediction = lt_prediction

        self.st_weight, self.lt_weight = self.calculate_weight(self.st_smape, self.lt_smape)
        self.agg_prediction = self.aggregate(self.st_weight, self.lt_weight, st_prediction, lt_prediction)


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




