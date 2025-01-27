import os
import matplotlib.pyplot as plt
from confluent_kafka import Producer as ConfluentProducer
from confluent_kafka.admin import AdminClient
import json
from config import config
from datetime import datetime, timedelta
from src.util import kafka_utils
import json

import logging
logger = logging.getLogger(__name__)

def create_trace_topic(args):

    logger.info(f"Using trace file: {config.trace}")

    # Delete Trace Topic if Exists
    bootstrap_server = kafka_utils.get_broker(args)
    trace_topic = config.kafka['trace_topic']
    partitions = config.kafka['trace_topic_partitions']
    if kafka_utils.check_topic_exists(bootstrap_server, trace_topic):
        logger.info("Trace Topic found.")
        kafka_utils.delete_topic(bootstrap_server, trace_topic)
    else:
        logger.info("No Trace Topic found.")
    kafka_utils.create_topic(bootstrap_server, trace_topic, partitions)


    # Initialize Metric Topic if supporting Offline Learning
    if config.trace_generator['lt_predictor_training_period'] > 0:
        metric_topic = config.kafka['metric_topic']
        partitions = config.kafka['metric_topic_partitions']
        
        if kafka_utils.check_topic_exists(bootstrap_server, metric_topic):
            logger.info("Metric Topic found.")
            #kafka_utils.delete_topic(bootstrap_server, metric_topic)
        else:
            logger.info("No Metric Topic found.")
            kafka_utils.create_topic(bootstrap_server, metric_topic, partitions)


    # Setup Kafka Producer    
    logger.info("Initializing Kafka Producer Connector")
    try:
        producer = ConfluentProducer({'bootstrap.servers': bootstrap_server})
    except:
        logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')

    # Setup Trace and Message Format
    current_timestamp = datetime.utcnow()
    timestamp = current_timestamp - timedelta(hours=config.trace_generator['lt_predictor_training_period'])
    five_minute_trace = f'{config.trace}_5min.csv'

    with open(f'traces/{five_minute_trace}', 'r') as tf:
        for line in tf:
            if "date,messages" in line: continue

            # Message Format: 2014-10-21 00:45:00,106987.59757204453
            load = trace_scale(float(line.split(",")[1]))
            message = {
                'trace': config.trace,
                'trace_file': five_minute_trace,
                'timestamp': f"{timestamp}",
                'load': load
            }
            if timestamp < current_timestamp:
                message["offline_training"] = True
                producer.produce(config.kafka['metric_topic'], json.dumps(message, indent=4, sort_keys=True))
            else:
                producer.produce(config.kafka['trace_topic'], json.dumps(message, indent=4, sort_keys=True))
            timestamp = timestamp + timedelta(seconds=config.trace_generator['seconds_between_traces'])

    producer.flush()
    logger.info("Trace Topic creation completed.")

def trace_scale(trace):
    
    # Variance Scale
    trace = (trace - config.trace_generator['mean']) * config.trace_generator['variance'] +  config.trace_generator['mean']

    # Scale to Target Mean
    trace = (trace / config.trace_generator['mean'])  * (config.trace_generator['avg_msg_per_second'] )

    return trace
