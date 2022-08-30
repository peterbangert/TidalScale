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

def create_trace_topic(args):

    if args.trace not in config.TRACE_FILES:
        raise ValueError(f'{args.trace} not found. Given Trace File not existent')

    # Delete Trace Topic if Exists
    bootstrap_server = kafka_utils.get_broker(args)
    if kafka_utils.check_topic_exists(bootstrap_server, config.KAFKA['trace_topic']):
        logger.info("Trace Topic found.")
        kafka_utils.delete_topic(bootstrap_server, config.KAFKA['trace_topic'])
    else:
        logger.info("No Trace Topic found.")

    # Setup Kafka Producer    
    logger.info("Initializing Kafka Producer Connector")
    try:
        producer = ConfluentProducer({'bootstrap.servers': bootstrap_server})
    except:
        logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')

    # Setup Trace and Message Format
    current_timestamp = datetime.now()
    timestamp = current_timestamp
    five_minute_trace = f'{args.trace}_5min.csv'

    with open(f'traces/{five_minute_trace}', 'r') as tf:
        for line in tf:
            if "date,messages" in line: continue

            # Message Format: 2014-10-21 00:45:00,106987.59757204453
            load = line.split(",")[1]
            message = f'{timestamp},{load}'
            producer.produce(config.KAFKA['trace_topic'], message.encode('utf-8'))
            timestamp = timestamp + timedelta(seconds=config.TRACE_GENERATOR['seconds_between_traces'])

    producer.flush()
    logger.info("Trace Topic creation completed.")
