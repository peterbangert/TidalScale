SHELL := /bin/bash
##
#    TRAFFIC GENERATOR DEPLOYMENT
#
##
PROJECT_NAME=thesistidalscale

deploy:
	${MAKE} kafka-create-data-topic
	${MAKE} kafka-create-trace-topic
	${MAKE} build
	${MAKE} push
	${MAKE} apply

redeploy:
	${MAKE} destroy
	${MAKE} kafka-delete-trace-topic
	${MAKE} kafka-create-trace-topic
	${MAKE} build
	${MAKE} push
	${MAKE} apply

delete-all-topics:
	${MAKE} kafka-delete-trace-topic
	${MAKE} kafka-delete-data-topic
	${MAKE} kafka-delete-metrics-topic
	${MAKE} kafka-delete-agg-prediction-topic

build:
	docker build -t eu.gcr.io/${PROJECT_NAME}/real-trace-generator .

push:
	docker push eu.gcr.io/${PROJECT_NAME}/real-trace-generator

apply:
	kubectl apply -f real-trace-generator-deployment.yaml

rollout:
	${MAKE} build
	${MAKE} push
	kubectl rollout restart deployment/real-trace-generator-deployment

destroy:
	kubectl delete deployments.apps real-trace-generator-deployment 

kafka-delete-trace-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic trace"

kafka-delete-metrics-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic metrics"

kafka-delete-agg-prediction-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic agg_prediction"

kafka-create-trace-topic:
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') && \
	cd app; python3 run.py -cte -b $$node_ip:31090
	
kafka-create-data-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --create --topic data --partitions 8 --replication-factor 1 --config retention.ms=600000"

kafka-delete-data-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic data"
