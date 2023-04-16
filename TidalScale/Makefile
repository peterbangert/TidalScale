SHELL := /bin/bash
##
#    TIDALSCALE DEPLOYMENT
#
##
NODE_IP=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') 
METRIC_GREP=$$(kafkacat -b $$NODE_IP:31090 -L | grep 'metric')
PROJECT_NAME=$$(gcloud config get-value project)

deploy:
	${MAKE} build
	${MAKE} push
	${MAKE} install

install:
	cd helm; helm install tidalscale .

uninstall:
	cd helm; helm uninstall tidalscale 

build:
	cd prediction-aggregator; docker build -t eu.gcr.io/${PROJECT_NAME}/prediction-aggregator .
	cd performance-meter; docker build -t eu.gcr.io/${PROJECT_NAME}/performance-meter . 
	cd metrics-reporter; docker build -t eu.gcr.io/${PROJECT_NAME}/metrics-reporter .
	cd autoscaling-controller; docker build -t eu.gcr.io/${PROJECT_NAME}/autoscaling-controller .

push:
	docker push eu.gcr.io/${PROJECT_NAME}/prediction-aggregator
	docker push eu.gcr.io/${PROJECT_NAME}/performance-meter
	docker push eu.gcr.io/${PROJECT_NAME}/metrics-reporter
	docker push eu.gcr.io/${PROJECT_NAME}/autoscaling-controller


## 
# 	Kafka Management
##
create-topics:
	${MAKE} kafka-create-data-topic
	${MAKE} kafka-create-metrics-topic
	${MAKE} kafka-create-agg-prediction-topic

delete-topics:
	${MAKE} kafka-delete-data-topic
	${MAKE} kafka-delete-metrics-topic
	${MAKE} kafka-delete-agg-prediction-topic

# Metrics Topic
kafka-create-metrics-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --create --topic metrics --partitions 1 --replication-factor 2"
	
kafka-delete-metrics-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic metrics"

# Aggregate Predictions
kafka-delete-agg-prediction-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic agg_prediction"

kafka-create-agg-prediction-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --create --topic agg_prediction --partitions 1 --replication-factor 2" 

# Data Topic
kafka-create-data-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --create --topic data --partitions 8 --replication-factor 1 --config retention.ms=600000"

kafka-delete-data-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic data"

##
#	Postgres Management
##
pg_backup:
	pg_dump -h localhost -U postgres -d tidalscale > performance-meter/pg_backup/$$(date +"%d%m%y_%H-%M-%S")_backup.psql
