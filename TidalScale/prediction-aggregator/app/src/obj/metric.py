import math
from datetime import datetime, timedelta
from config import config

import logging
logger = logging.getLogger(__name__)


class Metric:

    def __init__(self,metric_report):

        # Process Metrics
        self.msg_per_second, self.timestamp = 0, 0
        self.offline_training = False

        if 'offline_training' in metric_report:
            self.offline_training = True
            self.msg_per_second = float(metric_report['load'])
            timestamp = datetime.strptime(metric_report['timestamp'], config.config['time_fmt'])
            self.timestamp = timestamp
        
        else:
            for item in metric_report['kafkaMessagesPerSecond']:
                if item['metric']['topic'] == "data":
                    self.msg_per_second = float(item['value'][1])
                    timestamp = datetime.strptime(metric_report['timestamp'],config.config['time_fmt'])
                    self.timestamp = timestamp

        if math.isnan(self.msg_per_second) or self.msg_per_second == '' or self.msg_per_second == 0:
            raise Exception('Metric Report Error: null values')
