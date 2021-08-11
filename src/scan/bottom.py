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

# PDI forming a bottom and NDI forming a top on the uptrend
def checkBottomOnUptrend(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    isADXAbove25 = row.ADX >= 25
    maxNDI = round(max(list(df.loc[rowIndex:rowIndex+5].NDI)), 0)
    isNDIOnTop = (row.NDI < maxNDI) and (row.NDI >= 30) and (maxNDI >= round(row.ADX, 0))
    minPDI = min(list(df.loc[rowIndex:rowIndex+5].PDI))
    isPDIOnBottom = (row.PDI > minPDI) and (row.PDI < 25) and (row.PDI > prow.PDI)
    isHistogramIncreased = row.Histogram > prow.Histogram
    isAboveMA200 = row.Close > row.MA200
    minStoch = round(min(list(df.loc[rowIndex:rowIndex+5]['%D'])), 0)
    isStochOverSold = minStoch <= 25
    return isADXAbove25 and isNDIOnTop and isPDIOnBottom and isHistogramIncreased and isAboveMA200 and isStochOverSold

# PDI forming a bottom and NDI forming a top when break down MA200
def checkBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    maxNDI = round(max(list(df.loc[rowIndex:rowIndex+5].NDI)), 0)
    isNDIOnTop = (row.NDI < maxNDI) and (row.NDI >= 30) and (maxNDI >= round(row.ADX, 0))
    minPDI = min(list(df.loc[rowIndex:rowIndex+5].PDI))
    isPDIOnBottom = (row.PDI > minPDI) and (row.PDI < 25) and (row.PDI > prow.PDI)
    isHistogramIncreased = row.Histogram > prow.Histogram
    isBelowMA200 = row.Close < row.MA200
    minStoch = round(min(list(df.loc[rowIndex:rowIndex+5]['%D'])), 0)
    isStochOverSold = minStoch <= 25
    return isNDIOnTop and isPDIOnBottom and isHistogramIncreased and isBelowMA200 and isStochOverSold

# ADX forming a bottom while PDI increasing and NDI decreasing
def checkBottomOnCorrection(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    minADX = round(min(list(df.loc[rowIndex:rowIndex+5].ADX)), 0)
    isADXOnBottom = (row.ADX > prow.ADX) and (row.ADX < 25)
    isCrossDIs = (prow.PDI <= prow.NDI) and (row.PDI >= row.NDI)
    isPDIIncreased = (row.PDI > prow.PDI) and (row.PDI >= row.NDI)
    isHistogramIncreased = row.Histogram > prow.Histogram
    isMACDNegative = row.MACD_SIGNAL < 0
    isAboveMA200 = row.Close > row.MA200
    minStoch = round(min(list(df.loc[rowIndex:rowIndex+5]['%D'])), 0)
    isStochOverSold = minStoch <= 25
    return isADXOnBottom and isPDIIncreased and isHistogramIncreased and isAboveMA200 and isStochOverSold and isMACDNegative

def checkBottomOnCorrectionV2(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    minADX = round(min(list(df.loc[rowIndex:rowIndex+5].ADX)), 0)
    isADXOnBottom = (row.ADX > prow.ADX) and (row.ADX < 25)
    isCrossDIs = (prow.PDI <= prow.NDI) and (row.PDI >= row.NDI)
    isPDIIncreased = (row.PDI > prow.PDI) and (row.PDI >= row.NDI)
    isHistogramIncreased = row.Histogram > prow.Histogram
    isAboveMA200 = row.Close > row.MA200
    minStoch = round(min(list(df.loc[rowIndex:rowIndex+5]['%D'])), 0)
    isStochOverSold = minStoch <= 25
    return isADXOnBottom and isPDIIncreased and isHistogramIncreased and isAboveMA200 and isStochOverSold

def filterStocks(stocks, rowIndex):
    bottomOnUptrendStocks = []
    bottomStocks = []
    bottomCorrectionStocks = []
    bottomCorrectionStocksV2 = []
    date = ""
    for stock in stocks:
        # logger.info("Scanning {}".format(stock))
        df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
        # subDf = pd.read_csv("{}{}_{}.csv".format(intraday, smallTimeframe, stock))
        date = df.iloc[rowIndex].Date
        getIndicators(df)
        # getIndicators(subDf)
        if checkBottomOnUptrend(df, rowIndex):
            bottomOnUptrendStocks.append(stock)
        if checkBottom(df, rowIndex):
            bottomStocks.append(stock)
        if checkBottomOnCorrection(df, rowIndex):
            bottomCorrectionStocks.append(stock)
        if checkBottomOnCorrectionV2(df, rowIndex):
            bottomCorrectionStocksV2.append(stock)
    return (date, bottomOnUptrendStocks, bottomStocks, bottomCorrectionStocks, bottomCorrectionStocksV2)

def scan(stocks, rowIndex):
    (date, bottomOnUptrendStocks, bottomStocks, bottomCorrectionStocks, bottomCorrectionStocksV2) = filterStocks(stocks, rowIndex)
    print("Scanning on {}".format(date))
    if len(bottomOnUptrendStocks) > 0:
        print("Bottom on up trends")
        print(",".join(bottomOnUptrendStocks))
    if len(bottomStocks) > 0:
        print("Bottom stock (Break down MA200)")
        print(",".join(bottomStocks))
    if len(bottomCorrectionStocks) > 0:
        print("Bottom correction")
        print(",".join(bottomCorrectionStocks))
    if len(bottomCorrectionStocksV2) > 0:
        print("Bottom correction V2 (MACD SIGNAL can be above 0)")
        print(",".join(bottomCorrectionStocksV2))

def reportFoundStocks(stocks, rowIndex):
    (date, bottomOnUptrendStocks, bottomStocks, bottomCorrectionStocks, bottomCorrectionStocksV2) = filterStocks(stocks, rowIndex)
    message = "<H2>Scanning on {}</H2>".format(date)
    if len(bottomOnUptrendStocks) > 0:
        message = message + "<h3>Bottom on up trends:</h3>" + "\n"
        message = message + ",".join(bottomOnUptrendStocks)
    if len(bottomStocks) > 0:
        message = message + "<h3>Bottom stock (Break down MA200)</h3>" + "\n"
        message = message + ",".join(bottomStocks)
    if len(bottomCorrectionStocks) > 0:
        message = message + "<h3>Bottom correction:</h3>" + "\n"
        message = message + ",".join(bottomCorrectionStocks)
    if len(bottomCorrectionStocksV2) > 0:
        message = message + "<h3>Bottom correction V2 (MACD SIGNAL can be above 0):</h3>" + "\n"
        message = message + ",".join(bottomCorrectionStocksV2)
    message = message + "\n\n<b>Please check Stoch divergence, trendlines, MA and other resistances<b>\n"
    message = message + "<b>Exit trade early if you enter for Bottom stocks breaking down MA200<b>"
    sendEmail("Scan Stock Patterns", message, "html")

def checkStock(stock):
    df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
    # subDf = pd.read_csv("{}{}_{}.csv".format(intraday, smallTimeframe, stock))
    getIndicators(df)
    for rowIndex in reversed(range(len(df) - 200)):
        # if df.iloc[i].Date == "2021-07-15":
            patterns = []
            if checkBottomOnUptrend(df, rowIndex):
                patterns.append("Bottom on up trends")
            if checkBottom(df, rowIndex):
                patterns.append("Bottom stock (Break down MA200)")
            if checkBottomOnCorrection(df, rowIndex):
                patterns.append("Bottom correction")
            if checkBottomOnCorrectionV2(df, rowIndex):
                patterns.append("Bottom correction V2 (MACD SIGNAL can be above 0)")
            if len(patterns) > 0:
                print(df.iloc[rowIndex].Date, ",".join(patterns))

def scanStocks(stocks):
    scan(stocks, 0)

def scanHistoricalStocks(stocks):
    for i in (1, 5):
        scan(stocks, i)

if __name__ == "__main__":
    stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    if (len(sys.argv) == 1):    
        scanStocks(stocks)
    if (len(sys.argv) == 2):
        if(sys.argv[1] == 'history'):
            scanHistoricalStocks(stocks)
        if len(sys.argv[1]) == 3:
            print("Check stock")
            checkStock(sys.argv[1])
        if (sys.argv[1] == "email"):
            reportFoundStocks(stocks, 0)
