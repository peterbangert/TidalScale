
from config import config
from src.service.metric_consumer import MetricConsumer
from src.service.database import Database
from src.service.configuration_mgr_2d import ConfigurationManagerTwoDimensional
from src.service.configuration_mgr import ConfigurationManager
from src.obj.metric import Metric
import time
from datetime import datetime, timedelta
import json
import numpy as np
import math
from statistics import mean

import logging
logger = logging.getLogger(__name__)


class PerformanceMeter:

    def __init__(self ,args):
        logger.info("Initializing Metric Reporter")
        self.args = args
        self.consumer = MetricConsumer(args)
        self.configuration_mgr = ConfigurationManager(args)

    def run(self):

        # Main Logic Loop
        while True:
            metric_report = self.consumer.get_next_message()
            if metric_report:
                logger.info(f"Recieved Metric Report")
                metric = Metric(metric_report)
                if metric.no_nulls:
                    self.configuration_mgr.update_configurations(metric)
                else:
                    continue
            else:
                # Metrics are reported every 2 seconds
                time.sleep(1)
