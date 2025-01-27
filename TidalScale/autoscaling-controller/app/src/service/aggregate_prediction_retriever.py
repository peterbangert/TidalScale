from kafka import KafkaConsumer, TopicPartition
import json
from config import config
from src.util import kafka_utils
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

class PredictionRetriever:

    def __init__(self,args):
        logger.info("Initializing Aggregate Prediction Retriever")

        bootstrap_server = kafka_utils.get_broker(args)
        try:
            self.prediction_consumer = KafkaConsumer(
                bootstrap_servers=[bootstrap_server],
                value_deserializer=lambda m: json.loads(m.decode('ascii')),
                enable_auto_commit=False,
                consumer_timeout_ms=10000, # 10 Seconds
                auto_offset_reset='latest')

            tp = TopicPartition(config.kafka['agg_prediction'],0)
            self.prediction_consumer.assign([tp])

        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')

    def get_prediction(self):
        logger.info("Getting Aggregate Prediction")
        # dummy poll
        self.prediction_consumer.poll()
        # go to end of the stream
        self.prediction_consumer.seek_to_end()
        last_msg = None
        last_msg = next(self.prediction_consumer).value

        while datetime.strptime(last_msg['timestamp'], config.config['time_fmt']) < datetime.utcnow() - timedelta(seconds=config.config['metric_frequency']):
            last_msg = next(self.prediction_consumer).value

        logger.info(f"{last_msg}")

        return last_msg