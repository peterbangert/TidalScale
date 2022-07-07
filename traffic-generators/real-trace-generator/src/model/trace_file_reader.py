import config.config
import numpy as np
import pandas as pd

class TraceFileReader:

    def __init__(self,args):

        if args.trace not in config.config.TRACE_FILES:
            raise ValueError(f'{args.trace} not found. Given Trace File not existent')

        self.trace = args.trace
        self.five_minute_trace = f'{self.trace}_5min.csv'
        self.trace_file = open(f'traces/{self.five_minute_trace}', 'r')
        self.header_line = self.trace_file.readline()
        self.current_trace = self.trace_file.readline().split(",")
        self.next_trace = self.trace_file.readline().split(",")

    def increment_trace(self):
        self.current_trace = self.next_trace
        self.next_trace = self.trace_file.readline().split(",")

    def get_next_trace(self):
        return self.trace_file.readline().split(",")

    def get_per_second_trace(self):
        curr_trace_scaled = (float(self.current_trace[1]) / config.config.TRACE_GENERATOR['mean']) * config.config.TRACE_GENERATOR['avg_msg_per_second']
        next_trace_scaled = (float(self.next_trace[1]) / config.config.TRACE_GENERATOR['mean']) * config.config.TRACE_GENERATOR['avg_msg_per_second']
        #variance = abs(curr_trace_scaled - next_trace_scaled)
        x = [1,300] # 300 seconds in 5 minutes
        x_interp = range(1,300)
        self.increment_trace()
        return np.interp(x_interp, x, [curr_trace_scaled,next_trace_scaled])



