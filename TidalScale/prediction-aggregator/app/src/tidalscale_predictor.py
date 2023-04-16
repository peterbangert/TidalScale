from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from src.service.st_predictor import ShortTermPredictionModel
from src.service.lt_predictor import LongTermPredictionModel
from src.service.metric_consumer import MetricConsumer
from src.service.agg_prediction_producer import AggregatePredictionProducer
from src.service.prediction_aggregator import PredictionAggregator
from src.obj.metric import Metric
import time
import math
from datetime import datetime, timedelta
import traceback

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

class TidalScalePredictor:

    def __init__(self,args):
        logger.info("Initializing Prediction Aggregator")
        self.st_predictor = ShortTermPredictionModel(args)
        self.lt_predictor = LongTermPredictionModel(args)
        self.metric_consumer = MetricConsumer(args)
        self.trace_history = []
        self.prediction_producer = AggregatePredictionProducer(args)
        self.prediction_aggregator = PredictionAggregator(args)
        self.st_history = []
        self.lt_history = []
        self.timestamp = 0


    def run(self):
        # Main Logic Loop
        while True:
            metric_report = self.metric_consumer.get_next_message()
            if metric_report:
                try:
                    logger.info(f"Recieved Metric Report")
                    metric = Metric(metric_report)
                except Exception as e:
                    logger.error(f"{e}")
                    if logging.getLogger().level == logging.DEBUG:
                        print(traceback.format_exc())   
                    continue

                self.prediction_generator(metric)
            else:
                # Metrics are reported every 2 seconds
                time.sleep(1)

    def prediction_generator(self, metric):


        if metric.offline_training:
            self.lt_predictor.update_predictions(metric)
            return 0 

        
        st_smape = self.st_predictor.calculate_smape(metric)
        lt_smape = self.lt_predictor.calculate_smape(metric)


        self.st_predictor.update_predictions(metric)
        self.lt_predictor.update_predictions(metric) 
        ## Get Predictions from Both Models
        st_horizon, st_prediction = self.st_predictor.get_prediction()
        lt_horizon, lt_prediction = self.lt_predictor.get_prediction()

        logger.info(f"Recieved Predictions. ST: {st_prediction}, Horizon: {st_horizon}")
        logger.info(f"Recieved Predictions. LT: {lt_prediction}, Horizon: {lt_horizon}")

        prediction_data = {
            'timestamp': metric.timestamp,
            'msg_per_second': metric.msg_per_second,
            'st_horizon': st_horizon,
            'st_prediction': st_prediction,
            'lt_horizon': lt_horizon,
            'lt_prediction': lt_prediction,
            'st_smape': st_smape,
            'lt_smape': lt_smape
        }

        self.prediction_aggregator.update_prediction(prediction_data)

        if (self.prediction_aggregator.agg_prediction == 0):
            return 0

        message = {
            "messages_per_second": metric.msg_per_second, 
            "timestamp_utcnow": f"{datetime.utcnow()}",
            "timestamp": f"{metric.timestamp}",
            "prediction_horizon": f"{metric.timestamp + timedelta(seconds=config.config['rescale_window'])}",
            "aggregate_prediction": self.prediction_aggregator.agg_prediction,
            "st_weight": self.prediction_aggregator.st_weight,
            "lt_weight": self.prediction_aggregator.lt_weight,
            "st_smape": self.prediction_aggregator.st_smape,
            "lt_smape": self.prediction_aggregator.lt_smape,
            "st_prediction": self.prediction_aggregator.st_prediction,
            "lt_prediction": self.prediction_aggregator.lt_prediction
        }

        logger.info(message)

        self.prediction_producer.publish(message)


