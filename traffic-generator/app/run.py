from importlib.resources import path
import sys
import argparse
import logging
from logging.handlers import RotatingFileHandler
from config import config
from src.util import config_loader
import fileinput
from src.traffic_generator import TrafficGenerator
from src.util import create_trace_topic


def init_logger():
    ''' Configures Python Logging Facility
        - configure in config.py whether to write to logfile
        - if no, errors will be written to stderr
    '''
    
    # Path of logfile
    log_path = config.logger["log_path"]

    # Configure logger
    logFormatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Log to file?
    if config.logger["log_to_file"]:
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

    parser = argparse.ArgumentParser(description='Traffic Generator')
    parser.add_argument('-t','--trace', default=None, help=f'Load Trace model to use for traffic generator ' \
                                                                f'Possible Traces Include {config.trace_files}')
    parser.add_argument('-j','--job',default='WordCount',help='The processing job used by DSP system')
    parser.add_argument('--pubsub',default=False,action='store_true',help='Use Google PubSub')
    parser.add_argument('-l','--local',action='store_true',help='Run traffic generator locally, use local kafka broker')
    parser.add_argument('-b','--broker',help='<Address:Port> of kafka broker, default is config.py')
    parser.add_argument('-ct','--create-trace-topic',action='store_true',help='Initialize the Trace topic to current time')
    parser.add_argument('-cte','--create-trace-topic-exit',action='store_true',help='Initialize the Trace topic to current time')
    parser.add_argument('--config_path',default='/config/')
    args = parser.parse_args()
    config_loader.load_config(args=args)
    init_logger()

    if args.trace is not None:
        if args.trace not in config.trace_files:
            raise ValueError(f'Trace Argument non existent, trace file {args.trace} does not exist, please refer run.py -h for more info')
        else:
            setattr(config, "trace", args.trace)

    if args.create_trace_topic or config.create_trace_topic:
        create_trace_topic.create_trace_topic(args)

    if args.create_trace_topic_exit or config.create_trace_topic_exit:
        create_trace_topic.create_trace_topic(args)
        exit(0)
        

    # Read from stdin if input file not given as argument
    # infile = args.infile if args.infile else fileinput.input()

    traffic_generator = TrafficGenerator(args)
    traffic_generator.run()
