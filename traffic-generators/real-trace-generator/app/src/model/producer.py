#from kafka import KafkaProducer
from confluent_kafka import Producer as ConfluentProducer
import json
from config import config

import logging
logger = logging.getLogger(__name__)


class Producer:

    def __init__(self,args):
        logger.info("Initializing Traffic Producer")
        #self.producer = KafkaProducer(bootstrap_servers=[f'{config.KAFKA["broker_ip"]}:{config.KAFKA["port"]}'],
        #                              value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        if args.broker is not None:
            logger.info("Connecting to input Kafka Broker")
            bootstrap_server = args.broker    
        elif args.local:
            logger.info("Connecting to local Kafka Broker")
            bootstrap_server = f'{config.KAFKA_LOCAL["broker_ip"]}:{config.KAFKA_LOCAL["port"]}'    
        else:
            logger.info("Connecting to GCP Kafka Broker")
            bootstrap_server = f'{config.KAFKA["broker_ip"]}:{config.KAFKA["port"]}'
        try:
            self.producer = ConfluentProducer({'bootstrap.servers': bootstrap_server})
        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')


    def publish(self, message):
        self.producer.produce(config.KAFKA['topic'], message.encode('utf-8'))


    def pub_flush(self):
        self.producer.flush()