from importlib.resources import path
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
from config import config
import fileinput
from src.metric_reporter import MetricReporter
from src.util.delete_metrics_topic import delete_metrics_topic
import src.util.kafka_utils as kafka_utils


def init_logger():
    ''' Configures Python Logging Facility
        - configure in config.py whether to write to logfile
        - if no, errors will be written to stderr
    '''
    
    # Path of logfile
    log_path = config.LOGGER["log_path"]

    # Configure logger
    logFormatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Log to file?
    if config.LOGGER["log_to_file"]:
        fileHandler = RotatingFileHandler(log_path, mode="a", maxBytes=10e6, backupCount=5)
        fileHandler.setFormatter(logFormatter)
        logger.addHandler(fileHandler)
    else:
        consoleHandler = logging.StreamHandler(sys.stdout)
        consoleHandler.setFormatter(logFormatter)
        logger.addHandler(consoleHandler)
        logger.setLevel(logging.INFO)

 

if __name__ == "__main__":
    ''' Main method
        - Initializes logging facility
        - Initializes command line arguments
        - Initializes Log Parser
        Either stdin or -i|--infile can be read as input
    '''

    init_logger()
    parser = argparse.ArgumentParser(description='Traffic Generator')
    parser.add_argument('-l','--local',action='store_true',help='Run traffic generator locally, use local kafka broker')
    parser.add_argument('-b','--broker',help='<Address:Port> of kafka broker, default is config.py')
    parser.add_argument('-d','--delete_metric_topic', help='Delete Metric topic and re-initialize.')

    args = parser.parse_args()

    if args.delete_metric_topic:
        delete_metrics_topic(args)

    bootstrap_server = kafka_utils.get_broker(args)
    metric_topic = config.KAFKA['topic'] if not args.local else config.KAFKA_LOCAL['topic']
    if not kafka_utils.check_topic_exists(bootstrap_server, metric_topic):
        kafka_utils.create_topic(bootstrap_server, metric_topic)

    metric_reporter = MetricReporter(args)
    metric_reporter.run()
