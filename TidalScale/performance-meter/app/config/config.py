logger = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/app.log",
}

config = {
    "rescale_window" : 120,
    "metric_frequency" : 2
}

kafka = {
    "broker_ip": "kafka.default.svc.cluster.local",
    "port": 9092,
    "topic": 'metrics'
}

kafka_local = {
    "broker_ip": "localhost",
    "port": 9092,
    "topic": 'metrics'
}

thresholds = {
    "cpu_max": .8,
    "cpu_min": .2,
    "mem_max": .9,
    "rescale_cooldown": 30 # Seconds
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
    "table_schema": "CREATE TABLE configurations"
                    "(taskmanagers int, "
                    "cpu float, "
                    "parallelism int, "
                    "max_rate int NOT NULL, "
                    "PRIMARY KEY (taskmanagers, cpu), "
                    "created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL);",
    "insert": "INSERT INTO configurations ("
              "taskmanagers,cpu,parallelism,max_rate)"
              " values "
              "(" + 3*"%s, " + " %s );",        
    "update": "UPDATE configurations SET max_rate = %s WHERE taskmanagers = %s AND cpu = %s;",
    "check_max_rate": "SELECT max_rate FROM configurations WHERE taskmanagers = %s AND cpu = %s;",
    "select_all": "SELECT * FROM configurations;"
}
