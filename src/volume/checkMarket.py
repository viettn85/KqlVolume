import sys
sys.path.append('src/util')
import requests
import pandas as pd
import numpy as np
import operator
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *
import sys, os, glob
import traceback
np.seterr(divide='ignore', invalid='ignore')
from dotenv import load_dotenv
load_dotenv(dotenv_path='stock.env')
from analysisVolume import reportHourVolumes
import logging
import logging.config
logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

from utils import *

pd.set_option('mode.chained_assignment', None)
DATE_FORMAT = "%Y-%m-%d"
today = datetime.now().strftime(DATE_FORMAT)
data_location = os.getenv("data")

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
    industryDf = pd.read_csv(data_location + os.getenv("industries"), index_col="Stock")
    valueDf = pd.read_csv(data_location + os.getenv("high_value_stocks"), header=None)
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
            stockDf = pd.read_csv("{}{}.csv".format(data_location + os.getenv("data_active"), stock))
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
    print(pd.read_csv(data_location + os.getenv("high_value_stocks"), header=None).head(20))

def checkDuckyPattern(df):
    getIndicators(df)
    # print(df.head())
    criteria = []
    status = []
    criteria.append("Above MA200")
    if df.Close.iloc[0] > df.MA200.iloc[0]:
        status.append(True)
    else:
        status.append(False)
    criteria.append("Above MA50")
    if df.Close.iloc[0] > df.MA50.iloc[0]:
        status.append(True)
    else:
        status.append(False)
    criteria.append("Above MA20")
    if df.Close.iloc[0] > df.MA20.iloc[0]:
        status.append(True)
    else:
        status.append(False)
    criteria.append("Positive MACD")
    if df.MACD.iloc[0] > 0:
        status.append(True)
    else:
        status.append(False)
    criteria.append("Cross MACD")
    if df.Histogram.iloc[0] > 0:
        status.append(True)
    else:
        status.append(False)
    criteria.append("RSI Above 50")
    if df.RSI.iloc[0] >= 50:
        status.append(True)
    else:
        status.append(False)
    criteria.append("ADX Above 20")
    if round(df.ADX.iloc[0], 0) >= 20:
        status.append(True)
    else:
        status.append(False)
    criteria.append("ADX DI+ Above DI-")
    if df.PDI.iloc[0] >= df.NDI.iloc[0]:
        status.append(True)
    else:
        status.append(False)
    duckyDf = pd.DataFrame.from_dict({"Criteria": criteria, "Status": status})
    return duckyDf

def scanDucky():
    all_stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    high_value_stocks = list(pd.read_csv(data_location + os.getenv('high_value_stocks'), header=None)[0])
    duckyList = []
    candidateList = []
    for stock in high_value_stocks:
        data = data_location + os.getenv("data_realtime")
        duckyDf = checkDuckyPattern(pd.read_csv("{}{}.csv".format(data, stock)))
        metricCount = sum(list(duckyDf.Status))
        if metricCount == 8:
            duckyList.append(stock)
        elif metricCount == 7:
            candidateList.append(stock)
    if len(duckyList) > 0:
        print("There are {} stocks on the Ducky pattern".format(len(duckyList)))
        print(",".join(duckyList))
    if len(candidateList) > 0:
        print("There are {} candidates of the Ducky pattern".format(len(candidateList)))
        print(",".join(candidateList))

def checkStock(stock):
    data = data_location + os.getenv("data_realtime")
    df = pd.read_csv("{}{}.csv".format(data, stock))
    duckyDf = checkDuckyPattern(df)
    print(duckyDf)
    print("There are {}/8 metrics matched".format(sum(list(duckyDf.Status))))
    if all(list(duckyDf.Status)):
        print("A Ducky Pattern on 1D Chart! Please check more on 1H Chart")
    else:
        print("Not a Ducky Pattern")
    if stock in list(pd.read_csv(data_location + os.getenv("high_value_stocks"), header=None)[0]):
        print("\n\n{} is a high value stock".format(stock))
        df = pd.read_csv("{}{}.csv".format(data, stock))
        print("\nVALUES:")
        df["Value"] = round(df.Close * df.Volume / 1000000, 2)
        print(df[["Date", "Value", "Close", "Change"]].head())
    else:
        print("{} is NOT a high value stock".format(stock))
    # print("\nACTIVE VOLS:")
    # print(pd.read_csv("{}{}.csv".format(data_location + os.getenv("data_active"), stock), index_col = "Date").head(10))
    # print("\nTRADE COUNTS:")
    # today = datetime.now()
    # cashflowDf = pd.DataFrame()
    # for i in range(0, 14):
    #     date = (today + relativedelta(days=-i)).strftime(DATE_FORMAT)
    #     try:
    #         df = pd.read_csv("{}{}.csv".format(data_location + os.getenv("data_cashflow"), date))
    #         df['Date'] = date
    #         cashflowDf = cashflowDf.append(df[df.Stock == stock])
    #     except:
    #         dump = 0
    # print(cashflowDf[['Date', 'B', 'S', 'G', 'BB', 'BS', 'BG']])
    # print("\nHourly Cashflow Report:")
    # reportHourVolumes(stock)

if __name__ == '__main__':
    if sys.argv[1] == "ducky":
        scanDucky()
    if sys.argv[1] == "industries":
        checkIndustries()
    if sys.argv[1] == "industry":
        checkIndustry(sys.argv[2])
    # if sys.argv[1] == "active":
    #     checkActiveVol(sys.argv[2])
    # if sys.argv[1] == "cashflow":
    #     checkCashflow(sys.argv[2])
    if sys.argv[1] == "value":
        checkValue()
    if (len(sys.argv[1]) == 3) and ((sys.argv[1] != 'ato' and (sys.argv[1] != 'atc'))):
        checkStock(sys.argv[1])
