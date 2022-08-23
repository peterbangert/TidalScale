SHELL := /bin/bash
##
#    TRAFFIC GENERATOR DEPLOYMENT
#
##

deploy:

	${MAKE} kafka-create-data-topic
	${MAKE} kafka-create-trace-topic
	${MAKE} build
	${MAKE} push
	${MAKE} apply

build:
	docker build -t eu.gcr.io/msc-thesis-354309/real-trace-generator .

push:
	docker push eu.gcr.io/msc-thesis-354309/real-trace-generator

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

kafka-create-trace-topic:
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') && \
	cd app; python3 run.py -ct -b $$node_ip:31090
	
kafka-create-data-topic:
	kubectl exec -ti kafka-0 -- /bin/bash -c "unset JMX_PORT; /opt/bitnami/kafka/bin/kafka-topics.sh --zookeeper zookeeper:2181 --create --topic data --partitions 8 --replication-factor 2 --config retention.ms=600000"
