logger = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/app.log",
}

kafka = {
    "broker_ip": "kafka.default.svc.cluster.local",
    "port": 9092,
    "metric_topic": 'metrics',
    "metric_topic_partitions": 1
}

kafka_local = {
    "broker_ip": "localhost",
    "port": 9092,
    "metric_topic": 'metrics',
    "metric_topic_partitions": 1
}

prometheus = {
    "query_path": "/api/v1/query",
    "url": "prometheus-rest.default.svc.cluster.local:9090"
}

prometheus_queries = {
    "cpuUsage": "sum(flink_taskmanager_Status_JVM_CPU_Load) / sum(flink_jobmanager_numRegisteredTaskManagers)",
    "kafkaLag": "sum(flink_taskmanager_job_task_operator_KafkaSourceReader_KafkaConsumer_records_lag_max) / count(flink_taskmanager_job_task_operator_KafkaSourceReader_KafkaConsumer_records_lag_max)",
    "maxJobLatency": "max(flink_taskmanager_job_latency_source_id_operator_id_operator_subtask_index_latency)",
    "memUsage": "sum(flink_taskmanager_Status_JVM_Memory_Heap_Used / flink_taskmanager_Status_JVM_Memory_Heap_Committed) / sum(flink_jobmanager_numRegisteredTaskManagers)",
    "flinkNumRecordsOutPerSecond":"flink_taskmanager_job_task_numRecordsOutPerSecond",
    "kafkaMessagesPerSecond":"sum by (topic) (rate(kafka_server_brokertopicmetrics_messagesinpersec_count[2m]))",
    "flinkNumOfTaskManagers":"flink_jobmanager_numRegisteredTaskManagers",
    "flinkNumRecordsIn": "sum by (job_name) (rate(flink_taskmanager_job_task_numRecordsIn[2m]))",
    "flinkIngestionRate": "sum(flink_taskmanager_job_task_operator_KafkaSourceReader_KafkaConsumer_records_consumed_rate)"
}