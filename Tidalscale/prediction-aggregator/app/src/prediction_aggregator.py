from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from src.service.st_prediction_consumer import ShortTermPredictionConsumer
from src.service.lt_prediction_consumer import LongTermPredictionConsumer
from src.service.metric_consumer import MetricConsumer
from src.service.agg_prediction_producer import AggregatePredictionProducer
import time
import math
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
        self.st_consumer = ShortTermPredictionConsumer(args)
        self.lt_consumer = LongTermPredictionConsumer(args)
        self.metric_consumer = MetricConsumer(args)
        self.trace_history = []
        self.prediction_producer = AggregatePredictionProducer(args)




    def run(self):

        # Main Logic Loop
        while True:
            metric_report = self.metric_consumer.get_next_message()
            if metric_report:
                logger.info(f"Recieved Metric Report")
                self.process_metrics(metric_report)
            else:
                # Metrics are reported every 2 seconds
                time.sleep(1)

    def process_metrics(self, metric_report):

        msg_per_second = 0
        for item in metric_report['kafkaMessagesPerSecond']:
            if item['metric']['topic'] == "data":
                msg_per_second = float(item['value'][1])

        if math.isnan(msg_per_second) or msg_per_second == '' or msg_per_second == 0:
            return 0

        self.trace_history.append(msg_per_second)
        if len(self.trace_history) >= (config.CONFIG['rescale_window'] / config.CONFIG['metric_frequency']):
            self.trace_history.pop(0)

        st_prediction = self.st_consumer.get_prediction()
        lt_prediction = self.lt_consumer.get_prediction()

        logger.info(f"Recieved Predictions. ST: {st_prediction}, LT: {lt_prediction}")

        st_score = self.st_consumer.get_smape_score(self.trace_history)
        lt_score = self.lt_consumer.get_smape_score(self.trace_history)

        st_weight = st_score / (st_score + lt_score)
        lt_weight = lt_score / (st_score + lt_score)

        st_prediction_weighted = st_prediction * st_weight
        lt_prediction_weighted = lt_prediction * lt_weight

        aggregate_prediction = st_prediction_weighted + lt_prediction_weighted

        message = {
            "timestamp": datetime.utcnow(),
            "prediction_horizon": datetime.utcnow() + timedelta(seconds=config.CONFIG['rescale_window']),
            "aggregate_prediction": aggregate_prediction,
            "st_weight": st_weight,
            "lt_weight": lt_weight,
            "st_prediction": st_prediction,
            "lt_prediction": lt_prediction
        }

        self.prediction_producer.publish(message)
