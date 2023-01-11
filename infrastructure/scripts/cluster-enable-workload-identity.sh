#! /bin/bash

CLUSTER_NAME=$(cd k8s/terraform && terraform output cluster_name | tr -d '"')
ZONE=$(cd k8s/terraform && terraform output zone | tr -d '"')
REGION=$(cd k8s/terraform && terraform output region | tr -d '"')
POOL_NAME="$CLUSTER_NAME-standard-pool"
PROJECT_ID="thesistidalscale"
NAMESPACE="default"
KUBE_SERVICE_ACCOUNT='default'
TERRAFORM_USER="terraform"
TERRAFORM_SERVICE_ACCOUNT="$TERRAFORM_USER@$PROJECT_ID.iam.gserviceaccount.com"


echo "===== Enable Workload Identity to current cluster"

gcloud container clusters update $CLUSTER_NAME \
    --region=$ZONE \
    --workload-pool="${PROJECT_ID}.svc.id.goog"


echo "===== Add Workload metatdata to node-pool"


gcloud container node-pools update $POOL_NAME \
    --cluster=$CLUSTER_NAME \
    --zone=$ZONE \
    --workload-metadata=GKE_METADATA


echo "===== Add Workload Identity role to Terraform service account"
# Create Kubernetes Service Account
# Add Workload Identity User role to service account
gcloud iam service-accounts add-iam-policy-binding  \
	"${TERRAFORM_SERVICE_ACCOUNT}" \
    --role roles/iam.workloadIdentityUser \
    --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${NAMESPACE}/${KUBE_SERVICE_ACCOUNT}]"


echo "===== Anootating Kubernetes Service account with Gcloud service account"

kubectl annotate serviceaccount $KUBE_SERVICE_ACCOUNT \
    --namespace $NAMESPACE \
    iam.gke.io/gcp-service-account=$TERRAFORM_SERVICE_ACCOUNT
