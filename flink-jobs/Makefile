SHELL := /bin/bash
##
#    Flink Job Makefile
#
##

PROJECT_NAME=$$(gcloud config get-value project)

deploy:
	${MAKE} build
	${MAKE} push
	
build:
	cd flink-jobs; docker build -t eu.gcr.io/${PROJECT_NAME}/flink-jobs:statefulwordcount .

push:
	docker push eu.gcr.io/${PROJECT_NAME}/flink-jobs:statefulwordcount