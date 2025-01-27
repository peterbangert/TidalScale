# Tidalscale

> Predictive Autoscaler for cloud based Distributed Stream Processing Engines

 [![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

## Overall system design


<p align="center">
  <img width="900"  src="docs/img/Paper_Architecture-Page.png">
</p>


## Description

TidalScale, a predictive distributed stream processing autoscaler that proposes a refined and simplified model for managing DSP resources at runtime. Tidalscale uses aggregated short term and long term prediction model to anticipate future load. This enables it to choose resource efficient configurations of the DSP at runtime while maintaining quality of service (QoS). We show that TidalScale is capable of efficiently adapting DSP resources to varying loads.

Tidalscale strives to provide a platform agnostic autoscaling solution by analyzing metrics exposed from the container orchestrator system and the intermediate message brokering system. 

## Quick Start

1. Setup example [Infrastructure](./infrastructure/)
2. Deploy a [Traffic Generator](./traffic-generators)
2. Start [Tidalscale](./TidalScale/)


### System Architecture

Tidalscale requires interaction with various compoenents. 

- HDFS, for checkpointing the Stream Processing Job before scaling
- Kafka, a message brokering system to monitor traffic trends
- Prometheus, a monitoring system and timeseries database for observing systems health

<p align="center">
  <img width="430" height="300" src="docs/img/software-infra.png">
</p>


#### Broker

 
There are 2 Kafka topics used by the autoscaling system:

- `metrics` for message rate metrics
- `agg_prediction` for output results of the prediction models

#### Metrics

See the [Prometheus Postman collection](./Prometheus.postman_collection.json).

<details>
  <summary>Example of a Prometheus API request and response:</summary>

Here's the request. It is not a single HTTP request, but a separate request for each metric. Although it is technically possible to get all the metrics at once (as per [the documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)), we would have to do aggregations on our own. Having multiple queries is not a problem, however. We can simply specify a `time` field in the HTTP request to retrieve a consistent set of metrics.

```sh
request() {
	address="http://prometheus:30090"
	endpoint="/api/v1/query"
	url="${address}${endpoint}"
	time="2021-02-08T10:10:51.781Z"

	curl -Ss -X POST -F query="$1" -F time="$time" "$url" | jq
}

request "avg(avg by (operator_id) (flink_taskmanager_job_latency_source_id_operator_id_operator_subtask_index_latency{quantile=\"0.95\"}))"
request "avg(kafka_server_brokertopicmetrics_total_messagesinpersec_count)"
request kafka_controller_kafkacontroller_controllerstate_value
```

The response:

```
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": {},
        "value": [
          1612779051.781,
          "181.43333333333334"
        ]
      }
    ]
  }
}
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": {},
        "value": [
          1612779051.781,
          "112629192.33333334"
        ]
      }
    ]
  }
}
{
  "status": "success",
  "data": {
    "resultType": "vector",
    "result": [
      {
        "metric": {
          "__name__": "kafka_controller_kafkacontroller_controllerstate_value",
          "app_kubernetes_io_component": "kafka",
          "app_kubernetes_io_instance": "mpds",
          "app_kubernetes_io_managed_by": "Helm",
          "app_kubernetes_io_name": "kafka",
          "controller_revision_hash": "kafka-7dc6cd8b54",
          "helm_sh_chart": "kafka-11.8.2",
          "instance": "10.1.0.10:5556",
          "job": "kubernetes-pods",
          "kubernetes_namespace": "default",
          "kubernetes_pod_name": "kafka-1",
          "statefulset_kubernetes_io_pod_name": "kafka-1"
        },
        "value": [
          1612779051.781,
          "0"
        ]
      },
      {
        "metric": {
          "__name__": "kafka_controller_kafkacontroller_controllerstate_value",
          "app_kubernetes_io_component": "kafka",
          "app_kubernetes_io_instance": "mpds",
          "app_kubernetes_io_managed_by": "Helm",
          "app_kubernetes_io_name": "kafka",
          "controller_revision_hash": "kafka-7dc6cd8b54",
          "helm_sh_chart": "kafka-11.8.2",
          "instance": "10.1.1.6:5556",
          "job": "kubernetes-pods",
          "kubernetes_namespace": "default",
          "kubernetes_pod_name": "kafka-0",
          "statefulset_kubernetes_io_pod_name": "kafka-0"
        },
        "value": [
          1612779051.781,
          "0"
        ]
      },
      {
        "metric": {
          "__name__": "kafka_controller_kafkacontroller_controllerstate_value",
          "app_kubernetes_io_component": "kafka",
          "app_kubernetes_io_instance": "mpds",
          "app_kubernetes_io_managed_by": "Helm",
          "app_kubernetes_io_name": "kafka",
          "controller_revision_hash": "kafka-7dc6cd8b54",
          "helm_sh_chart": "kafka-11.8.2",
          "instance": "10.1.2.6:5556",
          "job": "kubernetes-pods",
          "kubernetes_namespace": "default",
          "kubernetes_pod_name": "kafka-2",
          "statefulset_kubernetes_io_pod_name": "kafka-2"
        },
        "value": [
          1612779051.781,
          "0"
        ]
      }
    ]
  }
}
```
</details>


