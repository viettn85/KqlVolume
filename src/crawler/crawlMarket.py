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
import math
from utils import *

load_dotenv(dotenv_path='stock.env')

data_location = os.getenv("data")
data_market = data_location + os.getenv('data_market')
tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()


def updatePriceAndVolume(fromDate, toDate):
    startTime = getEpoch(fromDate )
    endTime = getEpoch(toDate)
    all_stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    high_value_stocks = list(pd.read_csv(data_location + os.getenv('high_value_stocks'), header=None)[0])
    stocks = []
    ratios = []
    currentVols = []
    previousVols = []
    lastCloses = []
    closes = []
    changes = []
    current_time = getCurrentTime()
    # all_stocks = ['VND']
    for stock in all_stocks: 
        URL = "https://chartdata1.mbs.com.vn/pbRltCharts/chart/history?symbol={}&resolution=D&from={}&to={}".format(stock, startTime, endTime)
        response = requests.get(URL)
        # print(response.json())
        newDf = pd.DataFrame(response.json())
        newDf['t']=newDf.apply(lambda x: getDatetime(x.t)[0:10] ,axis=1)
        newDf['Change'] = 0
        newDf.rename(columns={"t": "Date", "c": "Close", "o": "Open", "h": "High", "l": "Low", "Change": "Change", "v": "Volume"}, inplace=True)
        newDf = newDf[['Date', 'Close', 'Open', 'High', 'Low', 'Change', 'Volume']]
        newDf.Volume = newDf.Volume * 10
        newDf.Volume = newDf.Volume.astype(int)
        newDf.sort_values(by="Date", ascending=False, inplace=True)
        newDf['Close_Shift'] = newDf.Close.shift(-1)
        newDf.Change = newDf.apply(lambda x: round((x.Close - x.Close_Shift)/x.Close_Shift * 100, 2) ,axis=1)
        newDf.drop('Close_Shift', axis=1, inplace=True)
        newDf[['Close', 'Open', 'High', 'Low']] = round(newDf[['Close', 'Open', 'High', 'Low']], 2)
        newDf.to_csv("{}{}.csv".format(data_market, stock), index=None)

if __name__ == "__main__":
    today = datetime.now(timezone(tz)).strftime(date_format)
    updatePriceAndVolume("2019-01-01", today)