SHELL := /bin/bash
##
#    TRAFFIC GENERATOR DEPLOYMENT
#
##
node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') 
TRACE_GREP=$$(kafkacat -b $$node_ip:31090 -L | grep 'trace')

deploy:
	ifeq ($(TRACE_GREP), )
		@echo "Trace topic non-existent"
	else
		@echo "Trace topic exists.. re-creating"
		${MAKE} kafka-delete-trace-topic
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
	python3 app/util/create_trace_topic.py