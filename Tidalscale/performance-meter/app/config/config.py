LOGGER = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/traffic_generator.log",
}

CONFIG = {
    "rescale_window" : 120,
    "metric_frequency" : 2
}

KAFKA = {
    "broker_ip": "kafka.default.svc.cluster.local",
    "port": 9092,
    "topic": 'metrics'
}

KAFKA_LOCAL = {
    "broker_ip": "localhost",
    "port": 9092,
    "topic": 'metrics'
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
    "table_schema": "CREATE TABLE configurations"
                    "(id SERIAL PRIMARY KEY,"
                    "num_taskmanager_pods int NOT NULL,"
                    "max_rate int NOT NULL,"
                    "parallelism int NOT NULL UNIQUE,"
                    "restart_time int,"
                    "catchup_time int,"
                    "recovery_time int,"
                    "created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL);",
    "insert": "INSERT INTO configurations ("
              "id,num_taskmanager_pods,max_rate,parallelism,restart_time,catchup_time,recovery_time)"
              " values "
              "(" + 6*"%s, " + " %s );",
              
    "update": "UPDATE configurations SET max_rate = %s WHERE id = %s;",
    "check_max_rate": "SELECT max_rate FROM configurations WHERE id = %s;",
    "select_all": "SELECT * FROM configurations;"
}
