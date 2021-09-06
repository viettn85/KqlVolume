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
    # print(changedPercent)
    reducedTwentyPercent = changedPercent >= 0.2
    # print(fiveRedCandle, changedPercent, reducedTwentyPercent)
    return fiveRedCandle or reducedTwentyPercent

def isOnDownTrend(df):
    row = df.iloc[0]
    return (row.Close < row.MA20) and (row.MA50 < row.MA200) and (row.MA20 < row.MA200)

def isDownAsAdx(df):
    row = df.iloc[0]
    prow1 = df.iloc[1]
    prow5 = df.iloc[5]
    isADXIncreasing = (row.ADX > prow1.ADX) and (row.ADX > prow5.ADX)
    isNDIIncreasing = (row.NDI > prow1.NDI) and (row.NDI > prow5.NDI)
    isADXAbove30 = row.ADX > 30
    isNDIAbove30 = row.NDI > 30
    return isADXIncreasing and isNDIIncreasing and (isADXAbove30 or isNDIAbove30)

def isDownAsAdx2(df):
    row = df.iloc[0]
    prow1 = df.iloc[1]
    isADXIncreasing = (row.ADX > prow1.ADX)
    isADXAbove30 = row.ADX > 30
    isNDIAbovePDI = row.NDI > row.PDI
    return isADXIncreasing and isNDIAbovePDI and isADXAbove30

def scan(stocks):
    downStocks = []
    downBelowMA200Stocks = []
    downtrend = []
    adx = []
    adx2 = []
    high_value_stocks = list(pd.read_csv(data_location + os.getenv('high_value_stocks'), header=None)[0])
    # stocks = ['VHM']
    for stock in stocks:
        df = pd.read_csv("{}{}_D.csv".format(data_realtime, stock))
        getIndicators(df)
        # if isDown(df) and (stock in high_value_stocks):
        #     if df.iloc[0].Close < df.iloc[0].MA200:
        #         downBelowMA200Stocks.append(stock)
        #     else:
        #         downStocks.append(stock)
        # if isOnDownTrend(df):
        #     downtrend.append(stock)
        if isDownAsAdx(df):
            adx.append(stock)
        if isDownAsAdx2(df):
            adx2.append(stock)
    if len(downStocks) > 0:
        print("Down stocks above MA200:")
        print(",".join(downStocks))
    if len(downBelowMA200Stocks) > 0:
        print("Down stocks under MA200:")
        print(",".join(downBelowMA200Stocks))
    if len(downtrend) > 0:
        print("Stock on down trend:")
        print(",".join(downtrend))
    if len(adx) > 0:
        print("Stock on adx:")
        print(",".join(adx))
    if len(adx2) > 0:
        print("Stock on adx2:")
        print(",".join(adx2))

if __name__ == "__main__":
    stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    # stocks = ['MST']
    if len(sys.argv) == 2:
        if sys.argv[1] == 'down':
            scan(stocks)
