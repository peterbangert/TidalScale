from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils

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
                config.KAFKA['prediction_agg'],
                bootstrap_servers=[bootstrap_server],
                value_deserializer=lambda m: json.loads(m.decode('ascii')),
                auto_offset_reset='latest')

        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')


    def get_prediction(self):
        last_msg = {}
        for msg in self.prediction_consumer:
            last_msg = msg.value
        return last_msg['prediction']