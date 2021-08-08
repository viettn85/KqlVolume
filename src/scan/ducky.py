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

def isUptrendCorrection(df, i):
    try:
        row = df.loc[i]
        prow = df.loc[i+1]
        srow = df.loc[i+15]
        maxMA = max(row.MA20, row.MA50)
        minMA = min(row.MA20, row.MA50)
        if (row.Close < maxMA) or (minMA < row.MA200) or (row.RSI < 48):
            return False
        minMACD = min(list(df.loc[i:i+15].MACD_SIGNAL))
        minStoch = min(list(df.loc[i:i+15]['%D']))
        # if row.Date == '2021-08-06':
        #     print(row)
        #     print(minStoch, srow['%D'], minMACD, srow.MACD_SIGNAL)
        #     print(((minStoch < srow['%D']) and (minStoch < 25) and (minStoch < row['%D'])))
        #     print(list(df.loc[i:i+10]['MACD_SIGNAL']))
        #     print(((minMACD < srow.MACD_SIGNAL) and (minMACD < row.MACD_SIGNAL)))
        if (((minStoch < srow['%D']) and (minStoch < 25) and (minStoch < row['%D'])) or ((minMACD < srow.MACD_SIGNAL) and (minMACD < row.MACD_SIGNAL))) and (prow.Close < max(prow.MA20, prow.MA50)):
            return True
        return False
    except:
        return False

def isDowntrendCorrection(df, i):
    try:
        row = df.loc[i]
        prow = df.loc[i+1]
        srow = df.loc[i+15]
        maxMA = max(row.MA20, row.MA50)
        minMA = min(row.MA20, row.MA50)
        if (row.Close > minMA) or (maxMA > row.MA200) or (row.RSI > 52):
            return False
        maxMACD = max(list(df.loc[i:i+15].MACD_SIGNAL))
        maxStoch = max(list(df.loc[i:i+15]['%D']))
        # if row.Date == '2020-02-25':
        #     print(row)
        #     print(maxStoch, srow['%D'], maxMACD, srow.MACD_SIGNAL)
        #     print(((maxStoch > srow['%D']) and (maxStoch > 75) and (maxStoch > row['%D'])))
            # print(list(df.loc[i:i+10]['MACD_SIGNAL']))
            # print(((maxMACD > srow.MACD_SIGNAL) and (maxMACD > row.MACD_SIGNAL)))
        if (((maxStoch > srow['%D']) and (maxStoch > 75) and (maxStoch > row['%D'])) or ((maxMACD > srow.MACD_SIGNAL) and (maxMACD > row.MACD_SIGNAL))) and (prow.Close > min(prow.MA20, prow.MA50)):
            return True
        return False
    except:
        return False

def shouldExitLong(df, i, subDf, position):
    row = df.iloc[i]
    newDf = subDf[subDf.Date > row.Date].tail(3)
    for i in reversed(range(len(newDf))):
        if (newDf.iloc[i].Close < newDf.iloc[i].MA20) and (row.MA50 > row.MA200) and (row.MA20 > row.MA50):
            if (not position["ShouldExitLong"]):
                position["UptrendCorrection"] = False
                position["ShouldExitLong"] = True
                return True
        else:
            position["ShouldExitLong"] = False
    return False

def shouldExitShort(df, i, subDf):
    row = df.iloc[i]
    newDf = subDf[subDf.Date > row.Date].tail(3)
    for i in reversed(range(len(newDf))):
        if (newDf.iloc[i].Close > newDf.iloc[i].MA20) and (row.MA50 < row.MA200) and (row.MA20 < row.MA50):
            return True
    return False

def findPatterns(df, i, subDf):
    row = df.loc[i]
    patterns = []
    histogramThreshold = max(df.Histogram) / 5
    macdThreshold = max(df.MACD) / 5
    macdSignalThreshold = max(df.MACD_SIGNAL) / 5
    if isSoftzone(row, histogramThreshold, macdThreshold, macdSignalThreshold):
        patterns.append("Softzone")
    # elif isCrossMA(row):
    #     patterns.append("CrossMA")
    if isUptrendCorrection(df, i):
        patterns.append("UptrendCorrection")
    if isDowntrendCorrection(df, i):
        patterns.append("DowntrendCorrection")
    # if shouldExitLong(df, i, subDf, position):
    #     patterns.append("ShouldExitLong")
    # if shouldExitShort(df, i, subDf, position):
    #     patterns.append("ShouldExitShort")
    return patterns

def scan(stocks, bigTimeframe, smallTimeframe):
    message = ""
    rowIndex = 0
    uptrendCorrections = []
    downtrendCorrections = []
    softzones = []
    for stock in stocks:
        # logger.info("Scanning {}".format(stock))
        df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
        # subDf = pd.read_csv("{}{}_{}.csv".format(intraday, smallTimeframe, stock))
        getIndicators(df)
        # getIndicators(subDf)
        patterns = findPatterns(df, rowIndex, [])
        # if len(patterns) > 0:
        #     print(stock, patterns)
        if "UptrendCorrection" in patterns:
            uptrendCorrections.append(stock)
        if "DowntrendCorrection" in patterns:
            downtrendCorrections.append(stock)
        if "Softzone" in patterns:
            softzones.append(stock)
    # return (uptrendCorrections, downtrendCorrections, softzones)
    if len(uptrendCorrections) > 0:
        print("Uptrend Corrections: {}".format(','.join(uptrendCorrections)))
    if len(downtrendCorrections) > 0:
        print("Downtrend Correction: {}".format(','.join(downtrendCorrections)))
    if len(softzones) > 0:
        print("Softzone: {}".format(','.join(softzones)))

def checkStock(stock):
    df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
    # subDf = pd.read_csv("{}{}_{}.csv".format(intraday, smallTimeframe, stock))
    getIndicators(df)
    for i in reversed(range(len(df) - 200)):
        patterns = findPatterns(df, i, [])
        if len(patterns) > 0:
            print(df.iloc[i].Date, patterns)

def scanStocks():
    if isWeekday():
        currentTime = getCurrentTime()
        if ((currentTime >= '09:15') and (currentTime <= '11:30')) or ((currentTime >= '13:00') and (currentTime <= '14:50')):
            stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
            scan(stocks, 'D', '60')

if __name__ == "__main__":
    if len(sys.argv) == 1:
        stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
        # stocks = ['VPH']
        scan(stocks, 'D', '60')

    if (len(sys.argv) == 2) and (len(sys.argv[1]) == 3):
        checkStock(sys.argv[1])