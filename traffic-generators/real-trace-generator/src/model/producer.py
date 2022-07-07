#from kafka import KafkaProducer
from confluent_kafka import Producer as ConfluentProducer
import json
from config import config

import logging
logger = logging.getLogger(__name__)


class Producer:

    def __init__(self):
        logger.info("Initializing Traffic Producer")
        #self.producer = KafkaProducer(bootstrap_servers=[f'{config.KAFKA["broker_ip"]}:{config.KAFKA["port"]}'],
        #                              value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        bootstrap_server = f'{config.KAFKA["broker_ip"]}:{config.KAFKA["port"]}'
        self.producer = ConfluentProducer({'bootstrap.servers': bootstrap_server})



    def publish(self, message):
        self.producer.produce(config.KAFKA['topic'], message.encode('utf-8'))


    def pub_flush(self):
        self.producer.flush()