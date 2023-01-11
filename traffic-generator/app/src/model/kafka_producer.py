#from kafka import KafkaProducer
from confluent_kafka import Producer as ConfluentProducer
import json
from config import config
from src.util import kafka_utils
from google.cloud import pubsub_v1
from concurrent import futures

import logging
logger = logging.getLogger(__name__)


class KafkaProducer:

    def __init__(self,args):
        logger.info("Initializing Traffic Producer")
    
        bootstrap_server = kafka_utils.get_broker(args)
        try:
            self.producer = ConfluentProducer({'bootstrap.servers': bootstrap_server})
        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')

    def publish(self, message):
        self.producer.produce(config.kafka['data_topic'], message.encode('utf-8'))

    def pub_flush(self):
        self.producer.flush()