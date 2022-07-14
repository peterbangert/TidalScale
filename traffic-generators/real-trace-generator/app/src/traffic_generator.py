

from config import config
from src.model.producer import Producer
from src.model.source import Source
from src.model.trace_file_reader import TraceFileReader
import time

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
        trace_start_time = time.time()
        load_trace = TraceFileReader(self.args)
        trace_arr = load_trace.get_per_second_trace()
        trace_index = 0
        curr_trace = trace_arr[trace_index]

        curr_time = trace_start_time
        msg_count = 0

        # Get a data point
        while True:

            # Produce it
            self.producer.publish(self.source.get_next_message())
            msg_count += 1

            # Increment Trace step 5 Minutes
            if trace_start_time - time.time() >= 300.0:
                trace_start_time = time.time()
                trace_arr = load_trace.get_per_second_trace()
                trace_index = 0
                curr_trace = trace_arr[trace_index]
                logger.info(f'New current Trace: {curr_trace}')
                msg_count = 0


            # Increment Trace step 1 Second
            if time.time() - curr_time  >= 1.0 or msg_count >= curr_trace:
                logger.info(f'{msg_count} messages delivered')
                self.producer.pub_flush()
                logger.info(time.time() - curr_time)
                # Didnt reach message goal for 1 second
                if time.time() - curr_time >= 1.0:
                    logger.info(f"Missed message p/s goal by {curr_trace - msg_count} messages")

                # Reached message goal before 1 second
                elif msg_count >= curr_trace:
                    logger.info(f"Waiting ~{1.0 - (time.time() - curr_time)} seconds")
                    time.sleep(1.0 - (time.time() - curr_time))

                curr_time = time.time()
                trace_index +=1
                if trace_index == len(trace_arr):
                    trace_arr = load_trace.get_per_second_trace()
                    trace_index = 0
                curr_trace = trace_arr[trace_index]
                logger.info(f'New current Trace: {curr_trace}')
                msg_count = 0


