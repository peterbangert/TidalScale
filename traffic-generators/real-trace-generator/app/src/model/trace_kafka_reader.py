from config import config
import numpy as np
import pandas as pd
from src.util import kafka_utils
from kafka import KafkaConsumer
from datetime import datetime
from datetime import timedelta

import logging
logger = logging.getLogger(__name__)



class TraceKafkaReader:

    def __init__(self,args):

        if args.trace not in config.TRACE_FILES:
            raise ValueError(f'{args.trace} not found. Given Trace File not existent')

        bootstrap_server = kafka_utils.get_broker(args)
        logger.info("Setting Up Kafka Consumer")
        try:
            self.consumer = KafkaConsumer(
                config.KAFKA['trace_topic'],
                bootstrap_servers=f'{bootstrap_server}',
                auto_offset_reset='earliest')
        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong: {bootstrap_server}')

        logger.info("Kafka consumer setup")

        current_timestamp = datetime.now()

        '''
        for msg in self.consumer:
            self.current_trace = msg.split(",")
            if current_timestamp >= datetime.strptime(self.current_trace[0]) - timedelta(seconds=config.TRACE_GENERATOR['seconds_between_traces']):
        '''

        
        self.current_trace = self.get_next_message(self.consumer)
        logger.info("Reading Trace entries")
        logger.info(f"{current_timestamp}  vs  {self.string_to_datetime(self.current_trace[0])}")
        while current_timestamp - timedelta(seconds=config.TRACE_GENERATOR['seconds_between_traces']) > self.string_to_datetime(self.current_trace[0]):
            self.current_trace = self.get_next_message(self.consumer)
        
        self.next_trace = self.get_next_message(self.consumer)

        logger.info(f"Current timestamp: {current_timestamp}, current trace: {self.current_trace[0]}, next trace: {self.next_trace[0]}")
        
        
    def get_next_message(self, consumer):
        return next(self.consumer).value.decode('ascii').split(",")
    
    def string_to_datetime(self, str_time):
        return datetime.fromisoformat(str_time)

    def increment_trace(self):
        self.current_trace = self.next_trace
        self.next_trace = self.get_next_message(self.consumer)
        current_timestamp = datetime.now()
        logger.info(f"Current timestamp: {current_timestamp}, current trace: {self.current_trace[0]}, next trace: {self.next_trace[0]}")

    def get_next_trace(self):
        return self.next_trace

    def get_current_trace(self):
        return self.current_trace

    def get_per_second_trace(self):

        current_timestamp = current_timestamp = datetime.now()
        diff = (self.string_to_datetime(self.next_trace[0]) - current_timestamp).seconds
        x = [1,diff]
        x_interp = range(1,diff)

        curr_trace_scaled = (float(self.current_trace[1]) / config.TRACE_GENERATOR['mean']) * config.TRACE_GENERATOR['avg_msg_per_second']
        next_trace_scaled = (float(self.next_trace[1]) / config.TRACE_GENERATOR['mean']) * config.TRACE_GENERATOR['avg_msg_per_second']
        #variance = abs(curr_trace_scaled - next_trace_scaled)

        return np.interp(x_interp, x, [curr_trace_scaled,next_trace_scaled])



