import pandas as pd
import numpy as np
from statsmodels.tsa.api import ExponentialSmoothing
import statsmodels
import pickle
import matplotlib.pyplot as plt
import time
import warnings
import itertools
from datetime import datetime, timedelta
from config import config

warnings.filterwarnings("ignore")

pd.options.display.max_rows = 9999
pd.options.display.max_columns = 100

import logging
logger = logging.getLogger(__name__)

class TripleExponentialSmoothing:

    def __init__(self):
        logger.info(f"Initializing TES Prediction Model")



    def optimizeHoltWinters(self, trace_history, mult):
        combinations = ["add", "mul"]
        best_model = None
        best_c = None
        best_aic = np.inf
        for c in combinations:
            model = ExponentialSmoothing(trace_history.load, seasonal_periods=mult * config.config['seasonal_period'], seasonal=c,
                                         initialization_method="estimated").fit()
            aic = model.aic
            if aic < best_aic:
                best_aic = aic
                best_model = model
                best_c = c
        return best_model, best_c


    def create_prediction(self, trace_history):
        model, hyper_params = self.optimizeHoltWinters(trace_history, config.config['traces_per_hour'])

        model = ExponentialSmoothing(trace_history.load, seasonal_periods=config.config['seasonal_period'] * config.config['traces_per_hour'],
                                     seasonal=hyper_params, initialization_method="estimated").fit()



        prediction = model.forecast(config.config['forecast_horizon'])

        if not isinstance(prediction.index[-1], datetime):
            logger.error(f"HORIZON ISNT DATETIME")
            logger.error(f"{trace_history}")

        # print(prediction)
        # print(prediction.index)
        # print(prediction.values)
            
        # Return Precitions and Horizon Timestamps
        return prediction.values, prediction.index

