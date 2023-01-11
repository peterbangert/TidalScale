#! /bin/bash


project="master-thesis-tidalscale"

if [ "$(gcloud config get-value account)" = "" ] || !  grep $project ~/.config/gcloud/application_default_credentials.json ; then
	echo "hello"
fi
exit 1

