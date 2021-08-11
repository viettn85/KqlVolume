import sys
sys.path.append('src/util')
import requests
import pandas as pd
import numpy as np
import os
from pytz import timezone
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *
from dotenv import load_dotenv
import logging
import logging.config
import math
from utils import *
import json
import schedule
import time

np.seterr(divide='ignore', invalid='ignore')
load_dotenv(dotenv_path='stock.env')

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

data_location = os.getenv("data")
data_realtime = os.getenv("data") + os.getenv("data_realtime")
tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

def isDown(df):
    fiveRedCandle = True
    for i in range(0, 5):
        # print(df.iloc[i].Close, df.iloc[i].Open)
        if df.iloc[i].Close >= df.iloc[i].Open:
            fiveRedCandle = False
            break
    maxHigh = max(list(df.loc[0:15].High))
    changedPercent = (maxHigh - df.iloc[0].Low)/df.iloc[0].Low
    reducedTwentyPercent = changedPercent > 20
    # print(fiveRedCandle, changedPercent, reducedTwentyPercent)
    return fiveRedCandle or reducedTwentyPercent

def scan(stocks):
    downStocks = []
    downBelowMA200Stocks = []
    for stock in stocks:
        df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
        getIndicators(df)
        if isDown(df):
            if df.iloc[0].Close < df.iloc[0].MA200:
                downBelowMA200Stocks.append(stock)
            else:
                downStocks.append(stock)
    if len(downStocks) > 0:
        print("Stock on down trend above MA200:")
        print(",".join(downStocks))
    if len(downBelowMA200Stocks) > 0:
        print("Stock on down trend under MA200:")
        print(",".join(downBelowMA200Stocks))

if __name__ == "__main__":
    stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    # stocks = ['MST']
    if len(sys.argv) == 2:
        if sys.argv[1] == 'down':
            scan(stocks)
