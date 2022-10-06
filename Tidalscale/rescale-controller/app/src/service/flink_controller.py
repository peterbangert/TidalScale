from kafka import KafkaConsumer
import json
from config import config as cfg
from src.util import kafka_utils
from kubernetes import client, config
from os import listdir
from os.path import isfile, join

from os import path

import yaml

import logging
logger = logging.getLogger(__name__)


class FlinkController:

    def __init__(self,args):
        logger.info("Initializing Flink Controller")
        self.depl_name = cfg.k8s['flink-taskmanager']
        self.namespace = cfg.k8s['namespace']
        config.load_kube_config()
        self.api = client.AppsV1Api()

    def check_flink_deployment(self):
        deployments = [x.metadata.name for x in self.api.list_namespaced_deployment(namespace=self.namespace).items]
        if cfg.k8s['flink-taskmanager'] not in deployments:
            logger.error("Flink Taskmanager not deployed")
            return False
        else:
            return True

    def deploy_flink(self):

        path = cfg.k8s['flink-reactive-path']
        for file in [f for f in listdir(path) if isfile(join(path, f))]:
            with open(path.join(path.dirname(path), file)) as f:
                dep = yaml.safe_load(f)
                k8s_apps_v1 = client.AppsV1Api()
                resp = k8s_apps_v1.create_namespaced_deployment(
                    body=dep, namespace=self.namespace)
                print("Deployment created. status='%s'" % resp.metadata.name)

    def rescale(self, target_parallelism):
        logger.info(f"Rescaling Flink Job: parallelism {target_parallelism}")
        api_response = self.api.patch_namespaced_deployment_scale(
            self.depl_name,
            self.namespace,
            {'spec': {'replicas': target_parallelism}})

        logger.info(f"Rescale API Response: f{api_response}")

        return 0

