#from kafka import KafkaProducer
from confluent_kafka import Producer as ConfluentProducer
import json
from config import config
from src.util import kafka_utils
from google.cloud import pubsub_v1
from concurrent import futures

import logging
logger = logging.getLogger(__name__)


class PubSubPublisher:

    def __init__(self,args):
        logger.info("Initializing Traffic Producer")
        self.batch = config.pubsub['batch']

        if self.batch:
            self.batch_settings = pubsub_v1.types.BatchSettings(
                max_messages=1000,  # default 100
                max_latency=1,  # default 10 ms
            )
            self.producer = pubsub_v1.PublisherClient(self.batch_settings)
            self.topic_path = self.producer.topic_path(config.pubsub['project_id'], config.pubsub['topic_id'])
            self.publish_futures = []
        else:
            self.producer = pubsub_v1.PublisherClient()
            self.topic_path = self.producer.topic_path(config.pubsub['project_id'], config.pubsub['topic_id'])


    def publish(self, message):
        if self.batch:
            publish_future = self.producer.publish(self.topic_path,message.encode('utf-8'))
            self.publish_futures.append(publish_future)
        else:
            self.producer.publish(self.topic_path,message.encode('utf-8'))
            

    def pub_flush(self):
        if self.batch:
            futures.wait(self.publish_futures, return_when=futures.ALL_COMPLETED)
            self.publish_futures = []
        else:
            return 0