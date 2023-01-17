#! /bin/bash

set -eu
set -x

project="$(gcloud config get-value project)"
terraform_user="terraform"
terraform_service_account="$terraform_user@$project.iam.gserviceaccount.com"

# Authenticate through gcloud if no gcp service account is used:
if [ "$(gcloud config get-value account)" = "" ] || ! grep $project ~/.config/gcloud/application_default_credentials.json ; then
	gcloud auth application-default login
fi

# Create Service Account for Terraform
if ! gcloud iam service-accounts list | grep -q "$terraform_service_account"; then
	gcloud iam service-accounts create "$terraform_user" \
		--description="This service account is used for Terraform" \
		--display-name="Terraform"
fi

# Create IAM policy binding
gcloud projects add-iam-policy-binding "$project" \
	--member="serviceAccount:${terraform_user}@${project}.iam.gserviceaccount.com" \
	--role="roles/owner"

# Add IAM policy binding service account user to user accounts
gcloud iam service-accounts add-iam-policy-binding \
	"${terraform_service_account}" \
	--member="user:$(gcloud config get-value account)" \
	--role="roles/iam.serviceAccountUser"

# Create service account key for Terraform
if [[ -s ./key.json ]]
then
	printf "IAM service account key exists"
else
	gcloud iam service-accounts keys create ./key.json \
		--iam-account "$terraform_service_account"
fi

exit 0
