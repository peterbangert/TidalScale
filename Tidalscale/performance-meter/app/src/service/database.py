from kafka import KafkaProducer
import json
from config import config
from src.util import kafka_utils
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
logger = logging.getLogger(__name__)


class Database():
    def __init__(self, args):
        logger.info("Initializing Database Connector")

        try:
            self.conn = psycopg2.connect(
                f"user='{config.POSTGRES['user']}' "
                f"host='{config.POSTGRES['host']}' "
                f"password='{config.POSTGRES['password']}'")
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            self.clear_database()
            self.create_database()
            self.conn = psycopg2.connect(
                f"dbname='{config.POSTGRES['database']}' "
                f"user='{config.POSTGRES['user']}' "
                f"host='{config.POSTGRES['host']}' "
                f"password='{config.POSTGRES['password']}'")
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            self.create_table()
        except Exception as e:
            logger.error(f'Error occured connecting to Postgres Database. Credentials may be wrong. Stack Trace:')
            logger.error(f"{e}")
            exit()

    def update_db(self, current_load):
        return 0

    def clear_database(self):
        self.cursor.execute(f"DROP DATABASE IF EXISTS {config.POSTGRES['database']};")

    def create_database(self):
        self.cursor.execute(f"CREATE DATABASE {config.POSTGRES['database']};")

    def create_table(self):
        self.cursor.execute(f"{config.POSTGRES['table_schema']}")

    def insert_performance(self, id, num_taskmanager_pods, max_rate, parallelism, restart_time=None, catchup_time=None, recovery_time=None):
        self.cursor.execute(config.POSTGRES['insert'],
                            (id, num_taskmanager_pods, max_rate, parallelism, restart_time, catchup_time, recovery_time))

    def update_performance(self, id, max_rate):
        self.cursor.execute(config.POSTGRES['update'], (max_rate,id))

    def check_max_rate(self, id):
        self.cursor.execute(config.POSTGRES['check_max_rate'], (str(id)))
        result = self.cursor.fetchall()
        return None if len(result) == 0 else result[0][0]

    def get_configurations(self):
        self.cursor.execute(config.POSTGRES["select_all"])
        return self.cursor.fetchall()
