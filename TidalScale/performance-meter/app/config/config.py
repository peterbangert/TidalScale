logger = {
    # Log console output to file?
    "log_to_file": False,
    # The logging file path for the python logger
    "log_path": "/tmp/app.log",
}

config = {
    "rescale_window" : 120,
    "metric_frequency" : 2,
    'alpha' : 0.2
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

postgres = {
    "host": "localhost",
    "user": "postgres",
    "password": "admin",
    "table": "configurations",
    "database": "tidalscale",

    ## Table Schema
    "table_schema": "CREATE TABLE configurations"
                    "(taskmanagers int, "
                    "cpu float, "
                    "parallelism int, "
                    "max_rate int NOT NULL, "
                    "ema_rate int, "
                    "PRIMARY KEY (taskmanagers, cpu), "
                    "created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL);",

    ## Insert Rates
    "insert_max_rate": "INSERT INTO configurations ("
              "taskmanagers,cpu,parallelism,max_rate)"
              " values "
              "(" + 3*"%s, " + " %s );",
    "insert_rates": "INSERT INTO configurations ("
              "taskmanagers,cpu,parallelism,max_rate,ema_rate)"
              " values "
              "(" + 4*"%s, " + " %s );",
    
    ## Update Rates
    "update_max_rate": "UPDATE configurations SET max_rate = %s WHERE taskmanagers = %s AND cpu = %s;",
    "update_ema_rate": "UPDATE configurations SET ema_rate = %s WHERE taskmanagers = %s AND cpu = %s;",
    "update_rates": "UPDATE configurations SET max_rate = %s, ema_rate = %s WHERE taskmanagers = %s AND cpu = %s;",

    ## Get Rates
    "check_max_rate": "SELECT max_rate FROM configurations WHERE taskmanagers = %s AND cpu = %s;",
    "get_rates": "SELECT max_rate, ema_rate FROM configurations WHERE taskmanagers = %s AND cpu = %s;",
    
    ## Select All
    "select_all": "SELECT * FROM configurations;"
}
