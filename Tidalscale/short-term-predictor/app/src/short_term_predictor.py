from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from src.service.metric_consumer import MetricConsumer
from src.service.prediction_producer import PredictionProducer
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
        self.metric_consumer = MetricConsumer(args)
        self.trace_history = []
        self.prediction_producer = PredictionProducer(args)
        self.spike_data = []
        self.linear_regression = []
        self.quadratic_regression = []
        self.MSE = 0



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
        for item in metric_report['kafkaMessagesPerSecond']:
            if item['metric']['topic'] == "data":
                msg_per_second = float(item['value'][1])

        if math.isnan(msg_per_second) or msg_per_second == '' or msg_per_second == 0:
            return 0

        ## SPIKE DETECTION
        ## Check if <8x MSE of Quadratic Regression
        if len(self.trace_history) > config.CONFIG['base_regression_length']:

            # Get Prediction for curtime, Current Time
            curr_prediction = self.linear_regression[0] * (len(self.trace_history)) + \
                              self.linear_regression[1]

            # Compare with current metric to see if outside MSE bounds
            if np.square(curr_prediction - msg_per_second) > config.CONFIG['MSE_bounds'] * self.MSE:
                self.spike_data.append(msg_per_second)
                if len(self.spike_data) > config.CONFIG['spike_window']:
                    logging.warning('Spike Detected')
                    self.trace_history = self.spike_data
                    self.spike_data = []
                else:
                    return
            else:
                self.spike_data = []


        # Add to Trace History
        self.trace_history.append(msg_per_second)
        if len(self.trace_history) >= (config.CONFIG['rescale_window'] / config.CONFIG['metric_frequency']):
            self.trace_history.pop(0)

        if len(self.trace_history) < config.CONFIG['base_regression_length']:
            return

        # Calculate Regressions
        y = self.trace_history
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

        message = {
            'st_prediction': prediction,
            "timestamp": f"{datetime.utcnow()}",
            "prediction_horizon": f"{datetime.utcnow() + timedelta(seconds=config.CONFIG['rescale_window'])}"
        }

        logger.info(message)

        self.prediction_producer.publish(message)
