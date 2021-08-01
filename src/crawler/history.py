import sys
sys.path.append('src/util')
import requests
import pandas as pd
import os
from pytz import timezone
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *
from dotenv import load_dotenv
import logging
import logging.config
from utils import *

load_dotenv(dotenv_path='stock.env')

data_location = os.getenv("data")
tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

def extractRatio(s, startDate, endDate):
    url = "https://api4.fialda.com/api/services/app/StockInfo/GetTradingChartData?symbol={}&interval=1d&fromTime={}T08:45:00.000&toTime={}T15:00:00.000".format(s, startDate, endDate)
    rsGetRquest= requests.get(url)
    tradingData = rsGetRquest.json()['result']
    if (tradingData is None) or (len(tradingData) == 0):
        return []
    df = pd.DataFrame(tradingData)[['tradingTime', 'buyVolRatio', 'buyVol', 'sellVol']]
    df.tradingTime = df.tradingTime.str[:10]
    df.buyVolRatio = df.buyVolRatio * 100
    df.rename(columns={"tradingTime": "Date", 'buyVolRatio': 'BuyVolRatio', "buyVol": "BuyVol", "sellVol": "SellVol"}, inplace=True)
    df[["BuyVolRatio", "BuyVol", "SellVol"]] = df[["BuyVolRatio", "BuyVol", "SellVol"]].fillna(0.0).astype(int)
    df.set_index("Date", inplace=True)
    return df

def extractHistoricalRatios():
    endDate = datetime.now(timezone(tz))
    startDate = endDate + relativedelta(months=-1)
    stocks = getStocks(os.getenv('all_stocks'))
    for s in stocks:
        volList = []
        df = extractRatio(s, startDate.strftime(date_format), endDate.strftime(date_format))
        if len(df) != 0:
            df.to_csv("{}data/active/{}.csv".format(data_location, s))
            logger.info("Extracted {} ratio".format(s))

if __name__ == "__main__":
    extractHistoricalRatios()