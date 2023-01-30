from kafka import KafkaProducer
import json
from config import config
from src.util import kafka_utils
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.errorcodes import UNIQUE_VIOLATION
from psycopg2 import errors
import logging
logger = logging.getLogger(__name__)


class Database():
    def __init__(self, args):
        logger.info("Initializing Database Connector")

        try:
            self.conn = psycopg2.connect(
                f"user='{config.postgres['user']}' "
                f"host='{config.postgres['host']}' "
                f"password='{config.postgres['password']}'")
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            
            if not self.db_exists():
                logger.info(f"Database {config.postgres['database']} does not exist. Creating")
                self.create_database()
            else:
                if args.clear:
                    self.clear_database()
                    self.create_database()
                logger.info(f"Database {config.postgres['database']} exists")

            self.conn = psycopg2.connect(
                f"dbname='{config.postgres['database']}' "
                f"user='{config.postgres['user']}' "
                f"host='{config.postgres['host']}' "
                f"password='{config.postgres['password']}'")
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            self.cursor = self.conn.cursor()
            
            if not self.table_exists():
                logger.info(f"Table {config.postgres['table']} does not exist. Creating")
                self.create_table()
            else:
                logger.info(f"Table {config.postgres['table']} exists")

        except Exception as e:
            logger.error(f'Error occured connecting to Postgres Database. Credentials may be wrong. Stack Trace:')
            logger.error(f"{e}")
            exit()

    def table_exists(self):
        self.cursor.execute(f"SELECT EXISTS(SELECT * FROM information_schema.tables where table_name = '{config.postgres['table']}');")
        return self.cursor.fetchone()[0]

    def db_exists(self):
        self.cursor.execute("SELECT datname FROM pg_database;")
        db_list = self.cursor.fetchall()
        return (config.postgres['database'],) in db_list

    def clear_database(self):
        self.cursor.execute(f"DROP DATABASE IF EXISTS {config.postgres['database']};")

    def create_database(self):
        self.cursor.execute(f"CREATE DATABASE {config.postgres['database']};")

    def create_table(self):
        self.cursor.execute(f"{config.postgres['table_schema']}")

    def insert_max_rate(self, taskmanagers, cpu, parallelism, max_rate):
        self.cursor.execute(config.postgres['insert'],
                            (taskmanagers, cpu, parallelism, max_rate))

    def update_max_rate(self, taskmanagers, cpu, max_rate):
        self.cursor.execute(config.postgres['update'], (max_rate, taskmanagers, cpu))

    ## Get Rates
    def check_max_rate(self, taskmanagers, cpu):
        try:
            self.cursor.execute(config.postgres['check_max_rate'], (str(taskmanagers),str(cpu)))
            result = self.cursor.fetchall()
            return None if len(result) == 0 else result[0][0]
        except Exception as e:
            logger.info(f"Querying Database failed, exception {e}")
            return None

    def get_rates(self, taskmanagers, cpu):
        try:
            self.cursor.execute(config.postgres['get_rates'], (str(taskmanagers),str(cpu)))
            result = self.cursor.fetchall()
            return (None,None) if len(result) == 0 else result[0]
        except Exception as e:
            logger.info(f"Querying Database failed, exception {e}")
            return None

    ## Insert Rates
    def insert_max_rate(self, taskmanagers, cpu, parallelism, max_rate):
        try:
            self.cursor.execute(config.postgres['insert_max_rate'],
                            (taskmanagers, cpu, parallelism, max_rate))
        except errors.lookup(UNIQUE_VIOLATION) as e:
            logger.info("Dirty Read occured, skipping..")


    def insert_rates(self, taskmanagers, cpu, parallelism, max_rate, ema_rate):
        try:
            self.cursor.execute(config.postgres['insert_rates'],
                            (taskmanagers, cpu, parallelism, max_rate, ema_rate))
        except errors.lookup(UNIQUE_VIOLATION) as e:
            logger.info("Dirty Read occured, skipping..")

    ## Update Rates
    def update_max_rate(self, taskmanagers, cpu, max_rate):
        self.cursor.execute(config.postgres['update_max_rate'], (max_rate, taskmanagers, cpu))

    def update_ema_rate(self, taskmanagers, cpu, ema_rate):
        self.cursor.execute(config.postgres['update_ema_rate'], (ema_rate, taskmanagers, cpu))

    def update_rates(self, taskmanagers, cpu, max_rate, ema_rate):
        self.cursor.execute(config.postgres['update_rates'], (max_rate, ema_rate, taskmanagers, cpu))

    ## Select All
    def get_configurations(self):
        self.cursor.execute(config.postgres["select_all"])
        return self.cursor.fetchall()

