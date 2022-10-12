SHELL := /bin/bash
##
#    TIDALSCALE DEPLOYMENT
#
##
node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') 
METRIC_GREP=$$(kafkacat -b $$node_ip:31090 -L | grep 'metric')

all:
	${make} images
	${make} install


images:
	${MAKE} build
	${MAKE} push


topic-management:
	ifeq ($(TRACE_GREP), )
		@echo "Metric topic non-existent"
	else
		@echo "Metric topic exists.. re-creating"
		${MAKE} kafka-delete-trace-topic
	${MAKE} kafka-create-metric-topic

build:
	cd prediction-aggregator; docker build -t eu.gcr.io/tidalscale-thesis/prediction-aggregator .
	cd performance-meter; docker build -t eu.gcr.io/tidalscale-thesis/performance-meter . 
	cd metrics-reporter; docker build -t eu.gcr.io/tidalscale-thesis/metrics-reporter .
	cd autoscaling-controller; docker build -t eu.gcr.io/tidalscale-thesis/autoscaling-controller .

push:
	docker push eu.gcr.io/tidalscale-thesis/prediction-aggregator
	docker push eu.gcr.io/tidalscale-thesis/performance-meter
	docker push eu.gcr.io/tidalscale-thesis/metrics-reporter
	docker push eu.gcr.io/tidalscale-thesis/autoscaling-controller


install:
	cd helm; helm install tidalscale .

rollout:
	${MAKE} build
	${MAKE} push
	kubectl rollout restart deployment/real-trace-generator-deployment

uninstall:
	cd helm; helm uninstall tidalscale 

kafka-delete-metrics-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic metrics"

kafka-create-metrics-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --create --topic metrics --partitions 1 --replication-factor 2 --config retention.ms=600000"


