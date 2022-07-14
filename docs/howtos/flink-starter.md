# Flink Howtos

- Start Flink cluster locally with Nodeport


```
$ ./bin/kubernetes-session.sh -Dkubernetes.cluster-id=my-first-flink-cluster -Dkubernetes.rest-service.exposed.type=NodePort

```

- Give default service account proper permissions to start resourcemanager (which watches, starts, deletes pods)

```
kubectl create clusterrolebinding flink-role-binding-default --clusterrole=edit --serviceaccount=default:default
```


- Package Flink Job

```
mvn clean package
```


