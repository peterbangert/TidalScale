from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from src.service.st_predictor import ShortTermPredictionModel
from src.service.lt_predictor import LongTermPredictionModel
from src.service.metric_consumer import MetricConsumer
from src.service.agg_prediction_producer import AggregatePredictionProducer
import time
import math
from datetime import datetime, timedelta

import logging
logger = logging.getLogger(__name__)

'''
Outgoing Data, 'st_prediction' topic example message:
{
    "occurredOn": timestamp of last observation
    "predictedWorkload":prediction
    "eventTriggerUuid": uuid of the last observation
    "eventType":"PredictionReported",
    "predictionBasedOnDateTime": timestamp of the predicted workload
    'uuid': event uuid           
}
'''

class PredictionAggregator:

    def __init__(self,args):
        logger.info("Initializing Prediction Aggregator")
        self.st_predictor = ShortTermPredictionModel(args)
        self.lt_predictor = LongTermPredictionModel(args)
        self.metric_consumer = MetricConsumer(args)
        self.trace_history = []
        self.prediction_producer = AggregatePredictionProducer(args)
        self.st_history = []
        self.lt_history = []




    def run(self):

        # Main Logic Loop
        while True:
            metric_report = self.metric_consumer.get_next_message()
            if metric_report:
                logger.info(f"Recieved Metric Report")

                self.process_metrics(metric_report)
            else:
                # Metrics are reported every 2 seconds
                time.sleep(1)

    def process_metrics(self, metric_report):

        msg_per_second = 0
        timestamp = 0
        
        offline_training = 'offline_training' in metric_report

        if 'load' in metric_report:
            msg_per_second = float(metric_report['load'])
            timestamp = datetime.strptime(metric_report['timestamp'], config.config['time_fmt'])
        else:
            for item in metric_report['kafkaMessagesPerSecond']:
                if item['metric']['topic'] == "data":
                    msg_per_second = float(item['value'][1])
                    timestamp = datetime.strptime(metric_report['timestamp'],config.config['time_fmt'])

        if math.isnan(msg_per_second) or msg_per_second == '' or msg_per_second == 0:
            return 0

        ## Append and Prune trace history
        self.trace_history = self.append_and_prune(timestamp, msg_per_second, self.trace_history)



        ## Get Predictions from Both Models
        st_horizon, st_prediction = self.st_predictor.get_prediction(timestamp,msg_per_second, offline_training)
        lt_horizon, lt_prediction = self.lt_predictor.get_prediction(timestamp,msg_per_second, offline_training) 

        logger.info(f"Recieved Predictions. ST: {st_prediction}, Horizon: {st_horizon}")
        logger.info(f"Recieved Predictions. LT: {lt_prediction}, Horizon: {lt_horizon}")


        if st_prediction != 0:
            self.st_history = self.append_and_prune(st_horizon, st_prediction, self.st_history)
            st_score = self.get_smape_score(self.st_history)

        else:
            if len(self.st_history) > 0:
                st_prediction = self.st_history[-1][1]
                st_score = self.get_smape_score(self.st_history)
            else:
                st_prediction = 0
                st_score = 0


        if lt_prediction != 0:
            self.lt_history = self.append_and_prune(lt_horizon, lt_prediction, self.lt_history)


            lt_score = self.get_smape_score(self.lt_history)
        else:
            if len(self.lt_history) > 0:
                lt_prediction = self.lt_history[-1][1]
                lt_score = self.get_smape_score(self.lt_history)
            else:
                lt_prediction = 0
                lt_score = 0

        ## Happens when no new LT prediction, and ST determined new data is outlier
        if st_score == 0 and lt_score ==0:
            logger.info("Returning, Likely no history for SMAPE to evaluate")
            return 0
        elif st_score == 0 or lt_score ==0:
            ## Calculate Weighted Scores
            st_weight = int(bool(st_score))
            lt_weight = int(bool(lt_score))
        else:
            ## Calculate Weighted Scores
            st_weight = 1 - (st_score / (st_score + lt_score))
            lt_weight = 1 - (lt_score / (st_score + lt_score))

        st_prediction_weighted = st_prediction * st_weight
        lt_prediction_weighted = lt_prediction * lt_weight

        ## Aggregate weighted Scores
        aggregate_prediction = st_prediction_weighted + lt_prediction_weighted

        message = {
            "messages_per_second": msg_per_second, 
            "timestamp_utcnow": f"{datetime.utcnow()}",
            "timestamp": f"{timestamp}",
            "prediction_horizon": f"{timestamp + timedelta(seconds=config.config['rescale_window'])}",
            "aggregate_prediction": aggregate_prediction,
            "st_weight": st_weight,
            "lt_weight": lt_weight,
            "st_smape": st_score,
            "lt_smape": lt_score,
            "st_prediction": st_prediction,
            "lt_prediction": lt_prediction
        }

        logger.info(message)

        if offline_training:
            return 0


        ## If Prediction is old, dont publish
        #if timestamp < datetime.utcnow() - timedelta(minutes=1):
        #    logger.info("Prediction too old, will not publish")
        #    return 0

        self.prediction_producer.publish(message)


    def append_and_prune(self, timestamp, data, tuple_list):
        tuple_list.append((timestamp, data))
        while len(tuple_list) > 0 and tuple_list[0][0] < tuple_list[-1][0] - timedelta(
                seconds=config.config['rescale_window'] * 2):
            tuple_list.pop(0)
        return tuple_list


    '''
        Linearly Decaying SMAPE Score
        Symmetric Mean Absolute Percentage Error (SMAPE)
    '''
    def get_smape_score(self, predictions):

        utc_now = datetime.utcnow()
        prediction_history = []

        for i in predictions:
            if i[0] < utc_now:
                prediction_history.append(i)

        if len(prediction_history) == 0:
            logger.info(f"GET SMAPE: No predition history")
            return 0

        if len(self.trace_history) == 0:
            logger.info(f"GET SMAPE: No Trace History history")
            return 0

        trace_prediction_zip = []
        trace_idx = 0
        pred_idx = 0
        for i in range(len(self.trace_history) + len(prediction_history)):

            trace = self.trace_history[trace_idx]
            prediction = prediction_history[pred_idx]

            if abs(trace[0] - prediction[0]).total_seconds() <= config.config['metric_frequency']:
                trace_prediction_zip.append((trace[1], prediction[1]))
                trace_idx += 1
                pred_idx += 1
            elif trace < prediction:
                trace_idx += 1
            else:
                pred_idx +=1

            if trace_idx == len(self.trace_history) or pred_idx == len(prediction_history):
                break

        n = len(trace_prediction_zip)

        if n == 0:
            logger.info(f"GET SMAPE: Trace/Prediction zip length 0")
            return 0

        smape = 0
        for i in range(len(trace_prediction_zip)):
            trace =trace_prediction_zip[i][0]
            pred = trace_prediction_zip[i][1]
            smape += (1/(n-i+1)) * (abs(trace - pred)/ (abs(trace)+abs(pred)))

        smape = smape / n

        if smape == 0:
            logger.info("============")
            logger.info(f"PREDICTIONS: {predictions}")
            logger.info(f"TRACE HISTORY: {self.trace_history}")
            logger.info("============")

        return smape