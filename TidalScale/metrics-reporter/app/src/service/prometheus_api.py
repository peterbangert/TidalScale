import json
from config import config
from prometheus_api_client import PrometheusConnect
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PrometheusAPI:

    def __init__(self,args):
        logger.info("Initializing Prometheus API")


        try:
            self.prometheus_client = PrometheusConnect(url=config.PROMETHEUS['url'], disable_ssl=True)
        except:
            logger.error(f'Error occured connecting to prometheus. Address may be wrong')

    def get_metrics(self):

        prom_rslt = config.PROMETHEUS_QUERIES.copy()
        for k,v in config.PROMETHEUS_QUERIES.items():
            prom_rslt[k] = self.prometheus_client.custom_query(query=v)

        prom_rslt['timestamp'] = f"{datetime.utcnow()}"

        return prom_rslt