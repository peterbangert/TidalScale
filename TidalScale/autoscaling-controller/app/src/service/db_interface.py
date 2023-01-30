from kafka import KafkaProducer
import json
from config import config
from src.util import kafka_utils
import numpy as np
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import math
from datetime import datetime
import numpy as np
import sklearn.linear_model

from mpl_toolkits.mplot3d import Axes3D

import logging
logger = logging.getLogger(__name__)



def get_configuration(expected_load):
    logger.info("Fetching Configurations from postgres")
    rows = []
    try:
        conn = psycopg2.connect(
            f"user='{config.postgres['user']}' "
            f"host='{config.postgres['host']}' "
            f"password='{config.postgres['password']}' "
            f"dbname='{config.postgres['database']}'")
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        cursor.execute(config.postgres["select_all"])
        rows = cursor.fetchall()
        conn.close()

    except Exception as e:
        logger.error(f'Error occured connecting to Postgres Database. Credentials may be wrong. Stack Trace:')
        logger.error(f"{e}")

    return config_3d_regression(rows, expected_load)

def config_3d_regression(rows, expected_load):

    if len(rows) == 0:
        return None
    
    logger.info(rows)

    x = [x[0] for x in rows]  # Taskmanager
    z = [x[1] for x in rows]  # CPU
    #y = [y[3] for y in rows]  # Max Rate
    y = [y[4] for y in rows]  # EMA Rate

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

        xz = np.asarray([list(a) for a in zip(x,z)])
        model = sklearn.linear_model.LinearRegression()
        model.fit(xz, y)
        coefs = model.coef_
        intercept = model.intercept_
        parallelism = int(((0.6)*coefs[1] + intercept - expected_load) / (-1 * coefs[0]))

    logger.info("-------------------")
    logger.info(f"Configuration Found: Parallelism {parallelism} for Expected Load: {expected_load}")
    logger.info("-------------------")

    return parallelism

def config_regression(rows, expected_load):

    parallelism = 0

    if len(rows) == 0:
        return None

    #logger.info(f"Rows: {rows}")
    #logger.info(f"Expected load: {expected_load}")

    x = [x[0] for x in rows]  # Parallelism
    y = [y[3] for y in rows]  # Max Rate

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
