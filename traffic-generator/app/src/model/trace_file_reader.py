import config.config
import numpy as np
import pandas as pd

"""
THIS CLASS IS DEPRECATED

This class is replaced by the TraceKafkaReader class. 

"""


class TraceFileReader:

    def __init__(self,args):

        self.trace = config.trace
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
        curr_trace_scaled = float(self.current_trace[1])
        next_trace_scaled = float(self.next_trace[1])
        #variance = abs(curr_trace_scaled - next_trace_scaled)
        x = [1,config.config.trace_generator['seconds_between_traces']] # 300 seconds in 5 minutes
        x_interp = range(1,config.config.trace_generator['seconds_between_traces'])
        self.increment_trace()
        return np.interp(x_interp, x, [curr_trace_scaled,next_trace_scaled])
