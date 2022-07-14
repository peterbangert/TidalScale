#! /bin/bash

CLUSTER_NAME=$(cd k8s/terraform && terraform output cluster_name | tr -d '"')
ZONE=$(cd k8s/terraform && terraform output zone | tr -d '"')
#POOL_NAME=$(gcloud container node-pools list --cluster $CLUSTER_NAME --zone $ZONE | grep -o "msc-thesis[a-z0-9-]*" )
POOL_NAME="$CLUSTER_NAME-standard-pool"
NUM_NODES=$(gcloud container node-pools describe $POOL_NAME --cluster $CLUSTER_NAME --zone $ZONE | grep NodeCount |grep -oP '\d')
NEW_NODE_COUNT=$(($NUM_NODES+1))

echo "Node Pool $POOL_NAME currently has $NUM_NODES, resizing to $NEW_NODE_COUNT"

gcloud container clusters resize $CLUSTER_NAME \
    --zone $ZONE \
    --node-pool $POOL_NAME \
    --num-nodes $NEW_NODE_COUNT

