from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils

import logging
logger = logging.getLogger(__name__)


class MetricConsumer:

    def __init__(self,args):
        logger.info("Initializing Traffic Producer")

        bootstrap_server = kafka_utils.get_broker(args)
        try:
            self.consumer = KafkaConsumer(
                config.kafka['metric_topic'],
                bootstrap_servers=[bootstrap_server],
                value_deserializer=lambda m: json.loads(m.decode('ascii')),
                auto_offset_reset='earliest')
        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')


    def get_next_message(self):
        return next(self.consumer).value

