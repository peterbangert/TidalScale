LOGGER = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/traffic_generator.log",
}

KAFKA = {
    "broker_ip": "kafka.default.svc.cluster.local",
    "port": 9092,
    "metric_topic": 'metrics',
    "st_prediction": "st_prediction",
    "lt_prediction": "lt_prediction",
    "agg_prediction": "agg_prediction",
    "lt_prediction_partitions": 1
}

KAFKA_LOCAL = {
    "broker_ip": "localhost",
    "port": 9092,
    "metric_topic": 'metrics',
    "st_prediction": "st_prediction",
    "lt_prediction": "lt_prediction",
    "agg_prediction": "agg_prediction"
}

CONFIG = {
    "rescale_window": 180, # seconds
    "metric_frequency": 2, # seconds
    'forecast_horizon': 3, # number of predictions in the future
    'traces_per_hour': 12,
    'trace_history_duration_hours': 14, # 3 days / 5
    'time_interval' : 60 # 300 for normal trace
}


