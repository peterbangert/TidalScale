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
    "agg_prediction_topic": "agg_prediction",
    "agg_prediction_topic_partitions": 1
}

kafka_local = {
    "broker_ip": "localhost",
    "port": 9092,
    "metric_topic": 'metrics',
    "agg_prediction_topic": "agg_prediction"
}

config = {
    "rescale_window": 180,
    "metric_frequency": 2,
    "lt_prediction_frequency": 60, # 300 for normal trace
    'forecast_horizon': 3, # number of predictions in the future
    'traces_per_hour': 12,
    'trace_history_duration_hours': 20, # 4 days / 5
    'seconds_between_traces' : 60, # 300 for normal trace
    'time_fmt' : '%Y-%m-%d %H:%M:%S.%f',
    "MSE_bounds": 8,
    "spike_window": 10,
    "base_regression_length": 10
}
