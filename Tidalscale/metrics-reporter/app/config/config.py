LOGGER = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/traffic_generator.log",
}

KAFKA = {
    "broker_ip": "kafka.default.svc.cluster.local",
    "port": 9092,
    "topic": 'data',
    "trace_topic": 'trace'
}

KAFKA_LOCAL = {
    "broker_ip": "localhost",
    "port": 9092,
    "topic": 'data'
}

TRACE_FILES = [
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

# Average message per second trace is 108k, configured average rate will scale trace files
TRACE_GENERATOR = {
    'avg_msg_per_second' : 100.0,
    'mean' : 108000.0,
    'std_deviation': 0.1,
    'seconds_between_traces': 60  # 300 is 5 minutes
}
