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
    "st_prediction_partitions" :1
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
    "rescale_window": 180,
    "metric_frequency": 2,
    "MSE_bounds": 8,
    "spike_window": 10,
    "base_regression_length": 10

}

