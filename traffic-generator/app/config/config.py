
logger = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/app.log",
}

kafka = {
    "broker_ip": "kafka.default.svc.cluster.local",
    "port": 9092,
    "data_topic": 'data',
    "trace_topic": 'trace',
    "trace_topic_partitions": 1,
    "metric_topic": "metrics",
    "metric_topic_partitions": 1
}

pubsub = {
    'batch':True,
    'topic_id': 'data',
    'project_id':'bangert-thesis'
}

kafka_local = {
    "broker_ip": "localhost",
    "port": 9092,
    "data_topic": 'data',
    "trace_topic": 'trace',
    "trace_topic_partitions": 1,
    "metric_topic": "metrics",
    "metric_topic_partitions": 1
}

trace_files = [
    'alibaba',
    'avazu',
    'google',
    'horton',
    'IoT',
    'retailrocket',
    'taxi',
    'wiki_de',
    'wiki_en'
    ]

broker = 'kafka'

# Configmap values for topic creation
create_trace_topic = False
create_trace_topic_exit = False

trace_file = "retailrocket"

# Average message per second trace is 108k, configured average rate will scale trace files
trace_generator = {
    'avg_msg_per_second' : 100000.0,
    'mean' : 108000.0,
    'std_deviation': 0.1,
    'seconds_between_traces': 60,  # 300 is 5 minutes
    "variance": 3,
    "lt_predictor_training_period": 20, # hours
    "pods": 5
}
