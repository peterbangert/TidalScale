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
    "trace_topic": 'trace',
    'agg_prediction': 'agg_prediction'
}

kafka_local = {
    "broker_ip": "localhost",
    "port": 9092,
    "metric_topic": 'metrics'
}

config = {
    "rescale_window": 180,
    "metric_frequency": 2,
    "time_fmt": '%Y-%m-%d %H:%M:%S.%f',
    "parallelization_upper_bound": 10,
    "parallelization_lower_bound": 1
}

thresholds = {
    "cpu_max": .8,
    "cpu_min": .4,
    "mem_max": .9,
}

# Determines where to load kube config
#   locally at $HOME/.kube/config 
#   or in-cluster config as ServiceAccount usage expects
deployment = 'local'

postgres = {
    "host": "localhost",
    "user": "postgres",
    "password": "admin",
    "table": "configurations",
    "database": "tidalscale",
    "select_all": "SELECT * FROM configurations;"
}

k8s = {
    "flink-taskmanager": 'flink-taskmanager',
    "namespace": 'default',
    "flink-reactive-path": "k8s/"
}