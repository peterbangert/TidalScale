

from config import config
from src.model.producer import Producer
from src.model.source import Source
from src.model.trace_kafka_reader import TraceKafkaReader
import time
from datetime import datetime

import logging
logger = logging.getLogger(__name__)


class TrafficGenerator:

    def __init__(self,args):
        logger.info("Initializing Traffic Generator")
        self.args = args
        self.producer = Producer(args)
        self.source = Source(args)

    def run(self):

        # Get the current trace
        trace_reader = TraceKafkaReader(self.args)
        trace_arr = trace_reader.get_per_second_trace()
        
        trace_index = 0
        curr_trace = trace_arr[trace_index]
        msg_count = 0
        curr_time = time.time()

        # Get a data point
        while True:

            # Produce it
            self.producer.publish(self.source.get_next_message())
            msg_count += 1

            # Increment Trace step 5 Minutes
            if datetime.now() >= trace_reader.string_to_datetime(trace_reader.get_next_trace()[0]):
                trace_reader.increment_trace()
                trace_arr = trace_reader.get_per_second_trace()
                trace_index = 0
                curr_trace = trace_arr[trace_index]
                logger.info(f'New current Trace Msg/second Goal: {curr_trace}')
                msg_count = 0


            # Increment Trace step 1 Second
            if time.time() - curr_time  >= 1.0 or msg_count >= curr_trace:
                
                # Flush Publisher, Report total Messages Delivered
                MESSAGEREPORT = f'{msg_count} Delivered Messages'
                self.producer.pub_flush()
                TIMEREPORT = f"Timelapse: {time.time() - curr_time}"
                
                TRACESEGMENTREPORT =  ""
                # Didnt reach message goal for 1 second
                if time.time() - curr_time >= 1.0:
                    TRACESEGMENTREPORT += f"Missed message p/s goal by {curr_trace - msg_count} messages"

                # Reached message goal before 1 second
                elif msg_count >= curr_trace:
                    TRACESEGMENTREPORT += f"Waiting ~{1.0 - (time.time() - curr_time)} seconds"
                    time.sleep(1.0 - (time.time() - curr_time))


                curr_time = time.time()
                trace_index +=1
                if trace_index == len(trace_arr):
                    logger.info("Reached end of interpolation array between trace periods, Decrementing Trace Index")
                    trace_index -=1

                # Publish Per/Second Report
                logger.info(f'{MESSAGEREPORT}. {TIMEREPORT}. {TRACESEGMENTREPORT}')

                curr_trace = trace_arr[trace_index]
                logger.info(f'New current Trace Msg/second Goal: {curr_trace}')
                msg_count = 0


