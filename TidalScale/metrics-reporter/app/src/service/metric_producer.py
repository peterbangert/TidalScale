from kafka import KafkaProducer
import json
from config import config
from src.util import kafka_utils

import logging
logger = logging.getLogger(__name__)


class MetricProducer:

    def __init__(self,args):
        logger.info("Initializing Traffic Producer")

        bootstrap_server = kafka_utils.get_broker(args)
        try:
            self.producer = KafkaProducer(bootstrap_servers=[bootstrap_server],
                                        value_serializer=lambda m: json.dumps(m).encode('ascii'))
        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')


    def publish(self, message):
        self.producer.send(config.kafka['metric_topic'], message)

