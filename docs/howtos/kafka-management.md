# Kafka Management

1. Access Kafka

- Enter a kafka broker

```
kubectl exec -ti kafka-0 bash
```

- Go to kafka/bin 

```
cd /opt/bitnami/kafka/bin
```

2. Manage Kafka

- List Topics

```
unset JMX_PORT; kafka-topics.sh --zookeeper zookeeper:2181 --list
```

- Describe Topics

```
kafka-topics.sh --zookeeper zookeeper:2181 --describe --topic test
```

- Delete Topic


```
kafka-topics.sh --zookeeper zookeeper:2181 --delete --topic test
```

3. Retention policy

- Create topic with retention policy

```
kafka-topics.sh --zookeeper zookeeper:2181 --create --topic test --partitions 8 --replication-factor 2 --config retention.ms=300000
```

- Edit Topic Retention Policy

```
kafka-topics.sh --zookeeper zookeeper:2181 --alter --topic test --config retention.ms=300000
```