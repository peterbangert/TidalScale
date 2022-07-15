SHELL := /bin/bash
##
#    TRAFFIC GENERATOR DEPLOYMENT
#
##

deploy:
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

