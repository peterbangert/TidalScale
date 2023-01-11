import os
import matplotlib.pyplot as plt
from confluent_kafka import Producer as ConfluentProducer
from confluent_kafka.admin import AdminClient
import json
from config import config
from datetime import datetime
from datetime import timedelta
from src.util import kafka_utils

import logging
logger = logging.getLogger(__name__)

def delete_metrics_topic(args):


    # Delete Metric Topic if Exists
    bootstrap_server = kafka_utils.get_broker(args)
    if kafka_utils.check_topic_exists(bootstrap_server, config.kafka['topic']):
        logger.info("Metrics Topic found.")
        kafka_utils.delete_topic(bootstrap_server, config.kafka['topic'])
    else:
        logger.info("No Metrics Topic found.")

