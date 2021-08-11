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

def checkDuckyPattern(df, rowIndex):
    getIndicators(df)
    criteria = []
    status = []
    criteria.append("Above MA200")
    if df.Close.iloc[rowIndex] > df.MA200.iloc[rowIndex]:
        status.append(True)
    else:
        status.append(False)
    criteria.append("Above MA50")
    if df.Close.iloc[rowIndex] > df.MA50.iloc[rowIndex]:
        status.append(True)
    else:
        status.append(False)
    criteria.append("Histogram increased")
    # if (df.Histogram.iloc[rowIndex] > df.Histogram.iloc[rowIndex + 1]) and (df.MACD_SIGNAL.iloc[rowIndex] < df.MACD_SIGNAL.iloc[rowIndex + 1]):
    if (df.Histogram.iloc[rowIndex] > df.Histogram.iloc[rowIndex + 1]):
        status.append(True)
    else:
        status.append(False)
    criteria.append("RSI Above 48")
    if df.RSI.iloc[rowIndex] >= 48:
        status.append(True)
    else:
        status.append(False)
    criteria.append("ADX Above 20")
    if round(df.ADX.iloc[rowIndex], 0) >= 17:
        status.append(True)
    else:
        status.append(False)
    criteria.append("ADX DI+ increased and DI- decreased")
    # if (df.PDI.iloc[rowIndex] >= df.PDI.iloc[rowIndex + 1]) and ((df.NDI.iloc[rowIndex] <= df.NDI.iloc[rowIndex + 1])) and ((df.PDI.iloc[rowIndex] <= df.NDI.iloc[rowIndex])):
    # print(df.PDI.iloc[rowIndex], df.PDI.iloc[rowIndex + 1], df.NDI.iloc[rowIndex], df.NDI.iloc[rowIndex + 1])
    if (round(df.PDI.iloc[rowIndex],0) >= round(df.PDI.iloc[rowIndex + 1], 0)) and ((round(df.NDI.iloc[rowIndex], 0) <= round(df.NDI.iloc[rowIndex + 1], 0))):
        status.append(True)
    else:
        status.append(False)
    duckyDf = pd.DataFrame.from_dict({"Criteria": criteria, "Status": status})
    # print(duckyDf)
    return duckyDf

def scan(stocks, rowIndex, bigTimeframe, smallTimeframe):
    message = ""
    uptrendCorrections = []
    downtrendCorrections = []
    softzones = []
    date = ""
    for stock in stocks:
        # logger.info("Scanning {}".format(stock))
        df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
        # subDf = pd.read_csv("{}{}_{}.csv".format(intraday, smallTimeframe, stock))
        date = df.iloc[rowIndex].Date
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
    print("Scan patterns of the market on {}".format(date))
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
        # if df.iloc[i].Date == "2021-06-14":
            duckyDf = checkDuckyPattern(df, i)
            if sum(list(duckyDf.Status)) == 6:
                print(df.iloc[i].Date, "True")

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
