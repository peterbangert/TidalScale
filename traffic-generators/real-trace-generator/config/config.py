LOGGER = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/traffic_generator.log",
}

KAFKA = {
    "broker_ip": "127.0.0.1",
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
    'avg_msg_per_second' : 100000.0,
    'mean' : 108000.0,
    'std_deviation': 0.1
}


