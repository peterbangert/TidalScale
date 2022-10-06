#! /bin/bash

set -eu
set -x

if [ ! -d "$FLINK_DIR" ]; then
	set +u
	echo "$0: FLINK_DIR is not a directory: $FLINK_DIR" >&2
	exit 1
fi

if [ "$FLINK_DOCKER_IMAGE" = "" ]; then
	set +u
	echo "$0: FLINK_DOCKER_IMAGE is not set" >&2
	exit 1
fi

flink_dir="$FLINK_DIR"
docker_image="$FLINK_DOCKER_IMAGE"

if ! kubectl describe serviceaccounts | grep -q '^Name:                flink-service-account$'; then
	kubectl create serviceaccount flink-service-account
	kubectl create clusterrolebinding flink-role-binding-flink --clusterrole=edit --serviceaccount=default:flink-service-account
fi

"$flink_dir/bin/flink" \
	run-application \
	--target kubernetes-application \
	-Dkubernetes.rest-service.exposed.type="NodePort" \
	-Dexecution.attached=false \
	-Dkubernetes.jobmanager.annotations=prometheus.io/scrape:'true',prometheus.io/port:'9999' \
	-Dkubernetes.taskmanager.annotations=prometheus.io/scrape:'true',prometheus.io/port:'9999' \
	-Dmetrics.latency.granularity=OPERATOR \
	-Dmetrics.latency.interval=1000 \
	-Dmetrics.reporters=prom \
	-Dmetrics.reporter.prom.class=org.apache.flink.metrics.prometheus.PrometheusReporter \
	-Dmetrics.reporter.prom.port=9999 \
	-Dmetrics.reporter.jmx.class=org.apache.flink.metrics.jmx.JMXReporter \
	-Dmetrics.reporter.jmx.port=8789 \
	-Dkubernetes.config.file=/home/pbangert/.kube/config \
	-Dkubernetes.service-account=flink-service-account \
	-Dkubernetes.cluster-id=flink-cluster \
	-Dkubernetes.container.image=eu.gcr.io/tidalscale-thesis/quickstart:latest \
	local:///opt/flink/usrlib/quickstart-0.1.jar
