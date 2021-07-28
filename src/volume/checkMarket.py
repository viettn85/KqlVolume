import sys
sys.path.append('src/util')
import requests
import pandas as pd
import operator
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *
import sys, os, glob
import traceback

from dotenv import load_dotenv
load_dotenv(dotenv_path='stock.env')

import logging
import logging.config
logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

from utils import *

pd.set_option('mode.chained_assignment', None)
DATE_FORMAT = "%Y-%m-%d"
today = datetime.now().strftime(DATE_FORMAT)


def getMessage(session, sellDf, buyDf):
    message = ""
    if len(buyDf) > 0:
        message = message + "\n<H2>Top {} Buying:</H2>".format(session)
        message = message + html_style_basic(buyDf)
    if len(sellDf) > 0:
        message = message + "\n<H2>Top {} Selling :</H2>".format(session)
        message = message + html_style_basic(sellDf)    
    return message

def getIndustryValues():
    industryDf = pd.read_csv(os.getenv("industries"), index_col="Stock")
    valueDf = pd.read_csv(os.getenv("high_value_stocks"), header=None)
    valueDf.columns = ['Stock', 'Value']
    valueDf.set_index('Stock', inplace=True)
    return pd.merge(valueDf, industryDf, on="Stock")

def checkIndustries():
    df = getIndustryValues()
    df = df.groupby(['Industry']).agg('sum')[['Value']]
    df.sort_values('Value', ascending=False, inplace=True)
    print(df.head())

def checkIndustry(industry):
    df = getIndustryValues()
    df = df[df.Industry == industry]
    df.sort_values('Value', ascending=False, inplace=True)
    print(df[['Value']].head(10))

def checkActiveVol(metric):
    asc = False
    if "-" in metric:
        asc = True
        metric = metric[1:]
    if metric == "ratio":
        column = "BuyVolRatio"
    if metric == "buy":
        column = "BuyVol"
    if metric == "sell":
        column = "SellVol"
    df = pd.DataFrame()
    stocks = getStocks(os.getenv('portfolio'))
    for stock in stocks:
        try:
            stockDf = pd.read_csv("{}{}.csv".format(os.getenv("data_active"), stock))
            stockDf['Stock'] = stock
            df = df.append(stockDf[0:1])
        except:
            a = 0
    df.sort_values(column, ascending=asc, inplace=True)
    print(df[['Stock', 'BuyVolRatio', 'BuyVol', 'SellVol']].head(20))

def checkCashflow(column):
    asc = False
    if "-" in column:
        asc = True
        column = column[1:]
    lastCashflow = getLastCashflow()
    df = pd.read_csv(lastCashflow, index_col='Stock')
    df.sort_values(column, ascending=asc, inplace=True)
    print(df.head(20))

def checkValue():
    print(pd.read_csv(os.getenv("high_value_stocks"), header=None).head(20))

def checkStock(stock):
    currentTime = getCurrentTime()
    if (datetime.today().weekday() < 5) and (currentTime > "09:15") and (currentTime < "20:30"):
        data = os.getenv("data_realtime")
    else:
        data = os.getenv("data_market")
    df = pd.read_csv("{}{}.csv".format(data, stock))
    if stock in list(pd.read_csv(os.getenv("high_value_stocks"), header=None)[0]):
        print("{} is a high value stock".format(stock))
        df = pd.read_csv("{}{}.csv".format(data, stock))
        print("\nVALUES:")
        df["Value"] = round(df.Close * df.Volume / 1000000, 2)
        print(df[["Date", "Value", "Close", "Change"]].head())
    else:
        print("{} is NOT a high value stock".format(stock))
    print("\nACTIVE VOLS:")
    print(pd.read_csv("{}{}.csv".format(os.getenv("data_active"), stock), index_col = "Date").head(10))
    print("\nTRADE COUNTS:")
    today = datetime.now()
    cashflowDf = pd.DataFrame()
    for i in range(0, 14):
        date = (today + relativedelta(days=-i)).strftime(DATE_FORMAT)
        try:
            df = pd.read_csv("{}{}.csv".format(os.getenv("data_cashflow"), date))
            df['Date'] = date
            cashflowDf = cashflowDf.append(df[df.Stock == stock])
        except:
            dump = 0
    print(cashflowDf[['Date', 'B', 'S', 'G', 'BB', 'BS', 'BG']])

if __name__ == '__main__':
    if sys.argv[1] == "industries":
        checkIndustries()
    if sys.argv[1] == "industry":
        checkIndustry(sys.argv[2])
    if sys.argv[1] == "active":
        checkActiveVol(sys.argv[2])
    if sys.argv[1] == "cashflow":
        checkCashflow(sys.argv[2])
    if sys.argv[1] == "value":
        checkValue()
    if (len(sys.argv[1]) == 3) and ((sys.argv[1] != 'ato' and (sys.argv[1] != 'atc'))):
        checkStock(sys.argv[1])
    
    
