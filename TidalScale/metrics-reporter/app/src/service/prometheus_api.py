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
            url = self.get_prometheus_url(args)
            self.prometheus_client = PrometheusConnect(url=url, disable_ssl=True)
        except:
            logger.error(f'Error occured connecting to prometheus. Address may be wrong')
    
    def get_prometheus_url(self,args):
        url = args.prometheus if args.prometheus else config.prometheus['url']
        url = url if url.startswith('http://') else 'http://' + url
        return url

    def get_metrics(self):

        prom_rslt = config.prometheus_queries.copy()
        for k,v in config.prometheus_queries.items():
            prom_rslt[k] = self.prometheus_client.custom_query(query=v)

        prom_rslt['timestamp'] = f"{datetime.utcnow()}"

        return prom_rslt
