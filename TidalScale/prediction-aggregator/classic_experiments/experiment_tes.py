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
warnings.filterwarnings("ignore")

pd.options.display.max_rows = 9999
pd.options.display.max_columns = 100

def show_ts(ts, forecast=None, forecast2 = None, title="Forecast Plot"):
    ax = ts.plot(label = "Observed", figsize=(10,3))
    if not (forecast is None):
        forecast.plot(ax=ax, label='Forecast')
        plt.legend()
    if not (forecast2 is None):
        forecast2.plot(ax=ax, label='Forecast')
        plt.legend()
        
    ax.set_xlabel('Date')
    ax.set_ylabel('Messages/Second')
    plt.title(title)
    plt.show()

def optimizeHoltWinters(ts, mult):
    combinations = ["add","mul"]
    best_model = None
    bestr_c = None
    best_aic = np.inf
    for c in combinations:
        model = ExponentialSmoothing(train.t, seasonal_periods=mult*24, seasonal=c, 
                                     initialization_method="estimated").fit()
        aic = model.aic
        if aic < best_aic:
            best_aic = aic
            best_model = model
            best_c = c
    return best_model, best_c
    
durations_df = pd.read_csv("results/durations.csv")

# Triple Exponential Smoothing aka Holt Winter's Exponential Smoothing
data_names = ["avazu","IoT","wiki_de","wiki_en","horton","retailrocket","taxi", "alibaba", "google"]

#sampling_rates = ["1h","15min","5min"]
sampling_rates = ["15min","5min"]
multipliers = [1,4,12]
forecast_horizons = [12,4,1]

train_test_split = 0.8

for data_name in data_names:
    for i,sampling_rate in enumerate(sampling_rates):
        print()
        print()
        print(data_name, sampling_rate)
        multiplier = multipliers[i]
        fh = forecast_horizons[i]
        df = pd.read_csv("../data/"+data_name+"_"+sampling_rate+".csv", index_col=0, parse_dates=True)

        df["t"] = df.messages
        df = df.drop(["messages"], axis=1)
        df = df.dropna()
        df = df.astype(np.int)

        train = df.iloc[:int(len(df)*train_test_split)]
        test = df.iloc[int(len(df)*train_test_split):]
        
        print("Train shape:", train.shape)
        print("Test shape:", test.shape)
        start_time = time.time()
        model, hyper_params = optimizeHoltWinters(train.t, multiplier)
        end_time = time.time()
        training_duration = end_time-start_time
        
        durations_df.loc[(durations_df.dataset == data_name) & (durations_df.sampling_rate == sampling_rate)\
                         , "ExpSmoothing"] = training_duration
        
        try:
            results_df = pd.read_csv("results/"+ data_name + "_" + sampling_rate + "_results.csv", index_col=0, parse_dates=True)
        except:
            results_df = test.t.to_frame()
            
        results_df["ExpSmoothing"] = 0
        results_df["ExpSmoothing"].iloc[:fh] = model.forecast(fh).values
        
        i = 1
        start_time = time.time()
        print(len(results_df))
        while i < len(results_df):
            ts = train.t.append(test.t.iloc[:i])
            model = ExponentialSmoothing(ts, seasonal_periods=24*multiplier, 
                             seasonal=hyper_params, initialization_method="estimated").fit()
            try:
                results_df["ExpSmoothing"].iloc[i:i+fh] += model.forecast(fh).values
            except ValueError:
                results_df["ExpSmoothing"].iloc[i:] += model.forecast(len(results_df)-i).values
            i += 1
            if i % 100 ==0:
                print(i,"/",len(test))
                print((datetime.now() + timedelta(hours=2)).strftime("%d.%m.%Y %H:%M:%S"))
        end_time = time.time()
        
        tuning_duration = (end_time - start_time) / len(results_df)
        durations_df.loc[(durations_df.dataset == data_name) & (durations_df.sampling_rate == sampling_rate)\
                         , "ExpSmoothing_tune"] = tuning_duration
        
        great_divider = list(range(1,len(results_df)+1))
        great_divider = list(map(lambda x: min(x,fh), great_divider))
        results_df["ExpSmoothing"] /= great_divider

        print(len(results_df))
        print("--------------------------------------------------------")
        print(results_df["ExpSmoothing"])

        show_ts(results_df.t, results_df.ExpSmoothing)
        results_df.to_csv("results/"+data_name+"_"+sampling_rate+"_results.csv")
        
        durations_df.to_csv("results/durations.csv", index=False)
        exit(1)