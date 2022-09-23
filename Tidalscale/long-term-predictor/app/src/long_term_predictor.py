from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from src.service.metric_consumer import MetricConsumer
from src.service.prediction_producer import PredictionProducer
from src.model.tes import TripleExponentialSmoothing
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
        self.metric_consumer = MetricConsumer(args)
        self.trace_history = []
        self.prediction_producer = PredictionProducer(args)
        self.prediction_model = TripleExponentialSmoothing()
        self.current_time = datetime.utcnow()
        self.time_fmt = '%Y-%m-%d %H:%M:%S.%f'



    def run(self):

        # Main Logic Loop
        while True:
            metric_report = self.metric_consumer.get_next_message()
            if metric_report:
                logger.info(f"Recieved Metric Report")
                self.create_prediction(metric_report)
            else:
                # Metrics are reported every 2 seconds
                time.sleep(1)

    def create_prediction(self, metric_report):

        msg_per_second = 0
        msg_timestamp = None
        if 'load' in metric_report:
            msg_per_second = float(metric_report['load'])
            msg_timestamp = datetime.strptime(metric_report['timestamp'],self.time_fmt)
        else:
            for item in metric_report['kafkaMessagesPerSecond']:
                if item['metric']['topic'] == "data":
                    msg_per_second = float(item['value'][1])
                    msg_timestamp = datetime.strptime(item['timestamp'],self.time_fmt)

        # Check for Null Values
        if math.isnan(msg_per_second) or msg_per_second == '' or msg_per_second == 0:
            return 0


        # Add to Trace History
        if msg_timestamp > datetime.utcnow() - timedelta(hours=config.CONFIG['trace_history_duration_hours']):

            # If trace history new
            if len(self.trace_history) == 0:
                self.trace_history.append((msg_timestamp, msg_per_second))

            # If New measurement is at least 'time_interval' different from last metric.
            #      - with error of 'metric_frequency'
            # Set current metric timestamp to exactly minute difference
            elif (msg_timestamp - self.trace_history[-1][0]).seconds > config.CONFIG['time_interval'] - config.CONFIG['metric_frequency']:
                msg_timestamp = self.trace_history[-1][0] + timedelta(seconds=config.CONFIG['time_interval'])
                self.trace_history.append((msg_timestamp,msg_per_second))

        else:
            return 0

        # Prune old Metrics
        while self.trace_history[0][0] < datetime.utcnow() - timedelta(
                hours=config.CONFIG['trace_history_duration_hours']):
            self.trace_history.pop(0)


        # 2 Season Cycles must be present in data to predict model on
        if len(self.trace_history) < 24 * config.CONFIG['traces_per_hour'] * 2:
            return 0

        pd_trace = pd.DataFrame(self.trace_history, columns=['date','load'])
        pd_trace.set_index('date',inplace=True)

        # Get Prediction
        prediction, prediction_horizon = self.prediction_model.create_prediction(pd_trace)

        logger.info(prediction)

        message = {
            'lt_prediction': prediction,
            "timestamp": f"{datetime.utcnow()}",
            "prediction_horizon": f"{prediction_horizon}"
        }

        logger.info(f"Publishing Prediction: \n{message}")

        self.prediction_producer.publish(message)
