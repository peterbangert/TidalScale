from confluent_kafka import Producer as ConfluentProducer
from confluent_kafka.admin import AdminClient
import json
from config import config

import logging
logger = logging.getLogger(__name__)


def get_broker(args):
    logger.info(f"Getting Bootstrap Server")

    if args.broker is not None:
        logger.info("Connecting to input Kafka Broker")
        bootstrap_server = args.broker    
    elif args.local:
        logger.info("Connecting to local Kafka Broker")
        bootstrap_server = f'{config.kafka_local["broker_ip"]}:{config.kafka_local["port"]}'    
    else:
        logger.info("Connecting to GCP Kafka Broker")
        bootstrap_server = f'{config.kafka["broker_ip"]}:{config.kafka["port"]}'

    return bootstrap_server

def check_topic_exists(bootstrap_server, topic):
    logger.info(f"Checking Existing Topic: {topic}")
    
    try:
        kafka_admin = AdminClient({'bootstrap.servers': bootstrap_server})
    except:
        logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')

    return topic in kafka_admin.list_topics().topics

def delete_topic(bootstrap_server, topic):
    logger.info(f"Deleting Topic: {topic}")
    
    try:
        kafka_admin = AdminClient({'bootstrap.servers': bootstrap_server})
    except:
        logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')

    fs = kafka_admin.delete_topics([topic], operation_timeout=30)

    # Wait for operation to finish.
    for tpc, f in fs.items():
        try:
            f.result()  # The result itself is None
            logger.info(f"Topic {tpc} deleted")
        except Exception as e:
            logger.info(f"Failed to delete topic {tpc}: {e}")


