

from config import config
from src.service.metric_producer import MetricProducer
from src.service.prometheus_api import PrometheusAPI
import time
from datetime import datetime
import json

import logging
logger = logging.getLogger(__name__)


class MetricReporter:

    def __init__(self,args):
        logger.info("Initializing Metric Reporter")
        self.args = args
        self.producer = MetricProducer(args)
        self.prometheus_api = PrometheusAPI(args)

    def run(self):

        while True:

            msg_json = self.prometheus_api.get_metrics()
            
            logger.info(json.dumps(msg_json, indent=4, sort_keys=True))
            self.producer.publish(msg_json)
            time.sleep(2)
