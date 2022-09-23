from importlib.resources import path
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
from config import config
import fileinput
from src.prediction_aggregator import PredictionAggregator



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
    args = parser.parse_args()


    prediction_aggregator = PredictionAggregator(args)
    prediction_aggregator.run()
