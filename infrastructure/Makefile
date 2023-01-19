SHELL := /bin/bash
##
#   CLUSTER MANAGEMENT
#
# 	cluster-create: create gke 3 node cluster
#	cluster-destroy: destory all
##

HELM_DIR=	helm/infrastructure
PROJECT_NAME= $$(gcloud config get-value project)

cluster-create:
	./scripts/cluster-setup-accounts.sh
	./scripts/cluster-setup-storage.sh
	./scripts/cluster-terraform.sh

cluster-destroy:
	cd terraform && terraform destroy -auto-approve

cluster-increase-nodepool:
	./scripts/cluster-resize.sh

cluster-enable-workload-identity:
	./scripts/cluster-enable-workload-identity.sh
##
#	SERVICE MANAGEMENT
#
#	services-install: setup all below
#	hdfs-install: setup hdfs
#	mpds-install: setup kafka, zookeeper, prometheus, grafana
#	flink-install: setup flink cluster, session mode
##

infra-install:
	cd ${HELM_DIR} && helm install infrastructure .

infra-uninstall:
	helm uninstall infrastructure

infra-upgrade:
	cd ${HELM_DIR} && helm upgrade infrastructure .


##
#	FLINK MANAGEMENT
#
#	flink-install: download tar,gz, unpack, execute scripts/flink-install.sh
#	flink-get-web-ui: get NodeIp:NodePort
##

FLINK_DIR=	flink-1.15.0
FLINK_TARBALL=	${FLINK_DIR}-bin-scala_2.12.tgz
FLINK_DOCKER_IMAGE=	eu.gcr.io/${PROJECT_NAME}/flink-engine-java11-1.0.0

${FLINK_TARBALL}:
	wget -O "$@" "https://downloads.apache.org/flink/flink-1.15.0/$@"

${FLINK_DIR}: ${FLINK_TARBALL}
	tar -xf "${FLINK_TARBALL}"

flink-install: ${FLINK_DIR}
	export FLINK_DIR="${FLINK_DIR}" && \
	export FLINK_DOCKER_IMAGE="${FLINK_DOCKER_IMAGE}" && \
	./scripts/flink-install.sh

flink-download:
	wget -O "${FLINK_TARBALL}" "https://downloads.apache.org/flink/flink-1.15.0/${FLINK_TARBALL}"
	tar -xf "${FLINK_TARBALL}"


flink-uninstall:
	kubectl get deployments | awk '/^flink-cluster.*/{ print $$1 }' | \
		xargs -n 1 kubectl delete deployment

flink-get-web-ui-reactive:
	node_port=$$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services flink-jobmanager-rest) && \
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}') && \
	echo "http://$$node_ip:$$node_port"

flink-get-web-ui:
	node_port=$$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].nodePort}" services flink-cluster-rest) && \
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}') && \
	echo "http://$$node_ip:$$node_port"

flink-application-mode-install: ${FLINK_DIR}
	export FLINK_DIR="${FLINK_DIR}" && \
	export FLINK_DOCKER_IMAGE="${FLINK_DOCKER_IMAGE}" && \
	./scripts/flink-application-mode-install.sh

flink-reactive-hpa-deploy:
	cd helm/flink-reactive-hpa/ && helm install flink-reactive-hpa .

flink-reactive-hpa-destroy:
	helm uninstall flink-reactive-hpa

flink-reactive-deploy:
	cd helm/flink-reactive/ && helm install flink-reactive .

flink-reactive-destroy:
	helm uninstall flink-reactive

##
#	POD MANAGEMENT
#
#	kafka-show-brokers: get nodeip and nodeport of brokers
#	grafana-get-web-ui: get nodeip and nodeport of grafana
##

kafka-show-brokers:
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') && \
	kafkacat -b $$node_ip:31090 -L | grep '  broker'

grafana-get-web-ui:
	node_port=30080 && \
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') && \
	echo "http://$$node_ip:$$node_port"

prometheus-get-web-ui:
	node_port=30090 && \
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') && \
	echo "http://$$node_ip:$$node_port"

kafka-show-topics:
	node_ip=$$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(.type=="ExternalIP")].address}') && \
	kafkacat -b $$node_ip:31090 -L 

















##
#	DEPRECATED
##

#${FLINK_TARBALL}:
#	wget -O "$@" "https://downloads.apache.org/flink/flink-1.15.0/$@"
#
#${FLINK_DIR}: ${FLINK_TARBALL}
#	tar -xf "${FLINK_TARBALL}"
#
#flink-fetch-dependencies: ${FLINK_DIR}
#
# Build the Flink job Docker image.
#flink-build-docker-image:
#	cd docker/flink && \
#	docker build -t ${FLINK_DOCKER_IMAGE} .

# Push the created image to the Container Registry.
#flink-push-docker-image:
#	gcloud auth configure-docker
#	cd docker/flink && \
#	docker push ${FLINK_DOCKER_IMAGE}


#flink-run-job-iot:
#	export FLINK_DIR="${FLINK_DIR}" && \
#	export FLINK_JOB_JAR="../iot-simulator/iot_vehicles_experiment/processor/target/processor-1.0-SNAPSHOT.jar" && \
#	./scripts/flink-run-job.sh \
#	$$(cat ../iot-simulator/args)
#
#flink-stop-jobs:
#	-${FLINK_DIR}/bin/flink list \
#		--target kubernetes-session \
#		-Dkubernetes.cluster-id=flink-cluster | \
#	grep -Eo '[0-9a-z]{32}' | \
#	xargs -n 1 ${FLINK_DIR}/bin/flink cancel
#
#FLINK_JOB_JAR=	covid-engine-2.3.2.jar

#flink-get-ids:
#	@printf '    job-id: '
#	@${FLINK_DIR}/bin/flink list --target kubernetes-session -Dkubernetes.cluster-id=flink-cluster | \
#		grep -Eo '[0-9a-z]{32}'
#	@printf '    jar-id: '
#	@node_port=$$(kubectl get --namespace default -o jsonpath="{.spec.ports[0].port}" services flink-cluster-rest) && \
#	node_ip=$$(kubectl get --namespace default -o jsonpath="{.status.loadBalancer.ingress[0].ip}" services flink-cluster-rest) && \
#	curl -Ss --location --request GET "http://$$node_ip:$$node_port/jars" | \
#		jq -r '.files[] | select(.name=="${FLINK_JOB_JAR}") | .id'
