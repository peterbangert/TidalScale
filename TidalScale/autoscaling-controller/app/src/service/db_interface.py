from kafka import KafkaProducer
import json
from config import config
from src.util import kafka_utils
import numpy as np
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import math

import logging
logger = logging.getLogger(__name__)



def get_configuration(expected_load):
    logger.info("Fetching Configurations from postgres")
    rows = []
    try:
        conn = psycopg2.connect(
            f"user='{config.POSTGRES['user']}' "
            f"host='{config.POSTGRES['host']}' "
            f"password='{config.POSTGRES['password']}' "
            f"dbname='{config.POSTGRES['database']}'")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(config.POSTGRES["select_all"])
        rows = cursor.fetchall()
        conn.close()

    except Exception as e:
        logger.error(f'Error occured connecting to Postgres Database. Credentials may be wrong. Stack Trace:')
        logger.error(f"{e}")

    return config_regression(rows, expected_load)

def config_regression(rows, expected_load):

    parallelism = 0

    if len(rows) == 0:
        return None

    #logger.info(f"Rows: {rows}")
    #logger.info(f"Expected load: {expected_load}")

    x = [x[0] for x in rows]  # Parallelism
    y = [y[2] for y in rows]  # Max Rate

    # Quotient Based Rule
    if len(x) == 1:
        parallelism = x[0] * math.ceil(expected_load/y[0])

    elif expected_load in y:
        return x[y.index(expected_load)]

    # If
    elif expected_load < min(y) and min(x) <= 2:
        parallelism = 1

    # Interpolate / Extrapolate
    else:
        fit = np.polyfit(x, y, 1)
        parallelism = math.ceil((expected_load - fit[1]) / fit[0])

    logger.info("-------------------")
    logger.info(f"Configuration Found: Parallelism {parallelism} for Expected Load: {expected_load}")
    logger.info("-------------------")

    return parallelism
