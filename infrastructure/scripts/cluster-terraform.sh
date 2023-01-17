#! /bin/bash
#
# Rerun this script in case of an error.

set -eu
set -x

project="$(gcloud config get-value project)"

# Set variables in Terraform files.
for file in backend.tf variables.tf; do
	(cd terraform && \
		sed "s|%%PROJECT_NAME%%|${project}|g" "${file}.in" > "$file")
done

# Put the key file into Terraform's directory.
ln -fs "$PWD/key.json" terraform/key.json

# Navigate to the folder k8s/terraform and initialize Terraform.
(cd terraform && terraform init)

# Validate the Terraform plan.
(cd terraform && terraform plan)

# Apply the Terraform plan and confirm the action.
(cd terraform && terraform apply -auto-approve)

# Configure kubectl with Terraform. tr -d removes extra quotations
(cd terraform && gcloud container clusters get-credentials \
	$(terraform output cluster_name | tr -d '"' ) \
	--zone $(terraform output zone | tr -d '"'))
