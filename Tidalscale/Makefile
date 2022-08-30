SHELL := /bin/bash
##
#    TIDALSCALE DEPLOYMENT
#
##
node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') 
METRIC_GREP=$$(kafkacat -b $$node_ip:31090 -L | grep 'metric')

all:
	${make} images
	${make} deploy


images:
	${MAKE} build
	${MAKE} push


deploy:
	ifeq ($(TRACE_GREP), )
		@echo "Metric topic non-existent"
	else
		@echo "Metric topic exists.. re-creating"
		${MAKE} kafka-delete-trace-topic
	${MAKE} kafka-create-metric-topic
	${MAKE} apply

build:
	cd long-term-predictor; docker build -t eu.gcr.io/msc-thesis-354309/long-term-predictor .
	cd short-term-predictor; docker build -t eu.gcr.io/msc-thesis-354309/short-term-predictor . 
	cd metrics-reporter; docker build -t eu.gcr.io/msc-thesis-354309/metrics-reporter .
	cd autoscaling-controller; docker build -t eu.gcr.io/msc-thesis-354309/autoscaling-controller .

push:
	docker push eu.gcr.io/msc-thesis-354309/long-term-predictor
	docker push eu.gcr.io/msc-thesis-354309/short-term-predictor
	docker push eu.gcr.io/msc-thesis-354309/metrics-reporter
	docker push eu.gcr.io/msc-thesis-354309/autoscaling-controller


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
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --create --topic metrics --partitions 8 --replication-factor 2 --config retention.ms=600000"


