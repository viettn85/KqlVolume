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

def isCrossMA(row):
    minMA = min(row.MA200, row.MA50, row.MA20)
    maxMA = max(row.MA200, row.MA50, row.MA20)
    if (abs(minMA - maxMA)/row.Close) <= float(os.getenv("ma_distance")):
        return True
    return False

def isSoftzone(row, histogramThreshold, macdThreshold, macdSignalThreshold):
    if isCrossMA(row) and (abs(row.Histogram) < histogramThreshold) \
        and (abs(row.MACD) < macdThreshold) and (abs(row.MACD_SIGNAL) < histogramThreshold):
        return True
    return False

def isUptrend(df, i):
    row = df.loc[i]
    if (row.MA20 > row.MA50) and (row.MA50 > row.MA200):
        return True
    return False

def isDowntrend(df, i):
    row = df.loc[i]
    if (row.MA20 < row.MA50) and (row.MA50 < row.MA200):
        return True
    return False

def isUpADX(df, i):
    row = df.loc[i]
    prow = df.loc[i + 1]
    if (prow.ADX < row.ADX) and (prow.PDI < row.PDI):
        return True
    else:
        return False

def isUpMACD(df, i):
    row = df.loc[i]
    prow = df.loc[i + 1]
    
    # Crossed MACD
    crossed = False
    days = -1
    for j in range (i, i+15):
        rowi = df.loc[j]
        rowi1 = df.loc[j]
        if (rowi.Histogram > 0) and (0 > rowi1.Histogram) and (rowi.MACD_SIGNAL > rowi1.MACD_SIGNAL):
            crossed = True
            days = j
            break
    possibleGap = ((row.MACD_SIGNAL > 0) and (days <= 5)) or ((row.MACD_SIGNAL < 0) and (days <= 15))
    crossMACD = crossed and possibleGap and (row.Histogram > prow.Histogram) and (row.MACD_SIGNAL > prow.MACD_SIGNAL)
    if (prow.MACD_SIGNAL < row.MACD_SIGNAL) and (prow.Histogram < row.Histogram):
        return True
    else:
        return False

def isBreakingMA20(df, i):
    row = df.loc[i]
    prow = df.loc[i + 1]
    belowMA20 = False
    date = df.iloc[i].Date
    for j in range(1, 10):
        if df.iloc[i+j].Close < df.iloc[i+j].MA20:
            belowMA20 = True
            break
    if (row.Close > row.MA20) and belowMA20:
        return True
    else: 
        return False

def isCuongPattern(df, i):
    row = df.loc[i]
    return isUpADX(df, i) and isUpMACD(df, i) and isBreakingMA20(df, i)

def findPatterns(df, i, subDf):
    row = df.loc[i]
    patterns = []
    if isCuongPattern(df, i):
        patterns.append("Cuong")
    return patterns

def scan(stocks, rowIndex, bigTimeframe, smallTimeframe):
    message = ""
    date = ""
    for stock in stocks:
        # logger.info("Scanning {}".format(stock))
        df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
        # subDf = pd.read_csv("{}{}_{}.csv".format(intraday, smallTimeframe, stock))
        date = df.iloc[rowIndex].Date
        getIndicators(df)
        # getIndicators(subDf)
        patterns = findPatterns(df, rowIndex, [])
        if len(patterns) > 0:
            print(date, patterns)

def checkStock(stock):
    df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
    getIndicators(df)
    for i in reversed(range(len(df) - 200)):
        if df.iloc[i].Date == '2019-10-24':
            patterns = findPatterns(df, i, [])
            if len(patterns) > 0:
                print(df.iloc[i].Date, patterns)

def scanStocks():
    if isWeekday():
        currentTime = getCurrentTime()
        if ((currentTime >= '09:15') and (currentTime <= '11:30')) or ((currentTime >= '13:00') and (currentTime <= '14:50')):
            stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
            scan(stocks, 0, 'D', '60')

if __name__ == "__main__":
    if len(sys.argv) == 1:
        stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
        # stocks = ['VPH']
        scan(stocks, 0, 'D', '60')
    if (len(sys.argv) == 2) and (len(sys.argv[1]) == 3):
        checkStock(sys.argv[1])
    if (len(sys.argv) == 2) and (sys.argv[1] == 'history'):
        stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
        for i in range(1, 4):
            scan(stocks, i, 'D', '60')