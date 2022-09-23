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

CONFIG = {
    "rescale_window": 120,
    "metric_frequency": 2
}

THRESHOLDS = {
    "cpu_max": .8,
    "cpu_min": .2,
    "mem_max": .9,
}

POSTGRES = {
    "host": "localhost",
    "user": "postgres",
    "password": "admin",
    "table": "configurations",
    "database": "tidalscale",
    "select_all": "SELECT * FROM configurations;"
}
