from kafka import KafkaConsumer
import json
from config import config
from src.util import kafka_utils
from datetime import datetime


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

class ShortTermPredictionConsumer:

    def __init__(self,args):
        logger.info("Initializing Long Term Prediction Consumer")

        self.short_term_history = []

        bootstrap_server = kafka_utils.get_broker(args)
        try:
            self.consumer = KafkaConsumer(
                config.KAFKA['st_prediction'],
                bootstrap_servers=[bootstrap_server],
                value_deserializer=lambda m: json.loads(m.decode('ascii')),
                auto_offset_reset='latest')
        except:
            logger.error(f'Error occured connecting to kafka broker. Address may be wrong {bootstrap_server}')

    '''
        Linearly Decaying SMAPE Score
        Symmetric Mean Absolute Percentage Error (SMAPE)
    '''
    def get_smape_score(self, real_load_traces):

        trace_prediction_zip = []
        trace_idx = 0
        pred_idx = 0
        utc_now = datetime.utcnow()
        lt_history = []
        for i in self.short_term_history:
            if datetime.strptime(i['predictionBasedOnDateTime']) < utc_now:
                lt_history.append(i)


        for i in range(max(len(real_load_traces),len(lt_history))):
            trace = real_load_traces[trace_idx]
            prediction = lt_history[pred_idx]
            if (trace - prediction).total_seconds() <= 2:
                trace_prediction_zip.append((trace, prediction))
            elif trace < prediction:
                trace_idx += 1
            else:
                pred_idx +=1

        n = len(trace_prediction_zip)
        smape = 0
        for i in range(len(trace_prediction_zip)):
            trace =trace_prediction_zip[i][0]
            pred = trace_prediction_zip[i][1]
            smape += (1/n-i+1) * (abs(trace - pred)/ (abs(trace)+abs(pred)))

        smape = smape / n
        return smape


    def get_prediction(self):
        logger.info("Getting ST Prediction")
        last_msg = {}
        msg = next(self.consumer).value
        logger.info(f"Got ST Prediction: {last_msg}")
        while not msg:
            last_msg = msg
            logger.info(f"Got ST Prediction: {last_msg}")
            self.short_term_history.append(last_msg)
            if len(self.short_term_history) > (config.CONFIG['rescale_window'] / config.CONFIG['metric_frequency'] * 2):
                self.short_term_history.pop(0)

            msg = next(self.consumer).value

        logger.info(f"Returning ST Prediction: {last_msg}")
        return last_msg
