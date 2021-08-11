import sys
sys.path.append('src/util')
sys.path.append('src/scan')
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
from ducky import *

np.seterr(divide='ignore', invalid='ignore')
load_dotenv(dotenv_path='stock.env')

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

data_location = os.getenv("data")
data_realtime = os.getenv("data") + os.getenv("data_realtime")
ducky_report = os.getenv("data") + os.getenv("ducky_report")
tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

def report():
    stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    # stocks = ['AAA']
    for stock in stocks:
        df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
        # subDf = pd.read_csv("{}{}_{}.csv".format(intraday, smallTimeframe, stock))
        getIndicators(df)
        dates = []
        corrections = []
        for i in reversed(range(len(df) - 200)):
            patterns = findPatterns(df, i, [])
            
            if (len(patterns) > 0) and (("UptrendCorrection" in patterns) or ("DowntrendCorrection" in patterns)):
                dates.append(df.iloc[i].Date)
                if "UptrendCorrection" in patterns:
                    corrections.append('UptrendCorrection')
                else:
                    corrections.append('DowntrendCorrection')
        df = pd.DataFrame.from_dict({"Date": dates, "Pattern": corrections})
        df.to_csv("{}{}.csv".format(ducky_report, stock), index=None)

def backtest():
    stocks = list(pd.read_csv(data_location + os.getenv('vn30'), header=None)[0])
    # stocks = ['AAA']
    evaluatedStocks = []
    corrects = []
    incorrects = []
    for stock in stocks:
        try:
            df = pd.read_csv("{}{}.csv".format(ducky_report, stock))
            intraday = pd.read_csv("{}{}.csv".format(data_realtime, stock))
            statuses = []
            changes = []
            for i in range(len(df)):
            # for i in range(3):
                # print(df.head())
                date = df.iloc[i].Date
                indexRow = intraday[intraday.Date == date].index[0]
                subDf = intraday.loc[indexRow - 10: indexRow]
                (status, change) = isCorrectPattern(subDf, df.iloc[i].Pattern)
                statuses.append(status)
                changes.append(change)
            df['Status'] = pd.Series(statuses)
            df['Change'] = pd.Series(changes)
            corrects.append(len(df[df.Status]))
            incorrects.append(len(df[df.Status == False]))
            evaluatedStocks.append(stock)
            df.to_csv("{}{}.csv".format(ducky_report, stock), index=None)
        except:
            print("No file for {}".format(stock))
    df = pd.DataFrame.from_dict({"Stocks": evaluatedStocks, "Correct": corrects, "Incorrect": incorrects})
    print("Correct {} and Incorrect {}".format(sum(df.Correct), sum(df.Incorrect)))
    print(df.head())
    df.to_csv("{}{}.csv".format(ducky_report, "backtest"))

def isCorrectPattern(subDf, pattern):
    start = subDf.iloc[-1].Close
    end = subDf.iloc[0].Close
    if pattern == "UptrendCorrection":
        maxClose = max(subDf.iloc[0:len(subDf) - 1].High)
        change = round((maxClose - start) / start, 2)
        if change >= 0.05:
            return (True, change)
        else:
            return (False, change)
    if pattern == "DowntrendCorrection":
        minClose = min(subDf.iloc[0:len(subDf) - 1].Low)
        change = round((minClose - start) / start, 2)
        if change <= -0.05:
            return (True, change)
        else:
            return (False, change)

if __name__ == "__main__":
    # report()
    backtest()
