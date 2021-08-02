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
data_realtime = data_location + os.getenv('data_realtime')
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
    # all_stocks = ['AAA']
    for stock in all_stocks: 
        URL = "https://chartdata1.mbs.com.vn/pbRltCharts/chart/history?symbol={}&resolution=D&from={}&to={}".format(stock, startTime, endTime)
        response = requests.get(URL)
        newDf = pd.DataFrame(response.json())
        newDf['t']=newDf.apply(lambda x: getDatetime(x.t)[0:10] ,axis=1)
        newDf['Change'] = 0
        newDf.rename(columns={"t": "Date", "c": "Close", "o": "Open", "h": "High", "l": "Low", "Change": "Change", "v": "Volume"}, inplace=True)
        newDf = newDf[['Date', 'Close', 'Open', 'High', 'Low', 'Change', 'Volume']]
        newDf.Volume = newDf.Volume * 10
        df = pd.read_csv("{}{}.csv".format(data_realtime, stock))
        # Remove the today data if existed
        df = df[df.Date != newDf.Date[0]]
        newDf.Change = round((newDf.Close.iloc[0] - df.Close.iloc[0]) / df.Close.iloc[0] * 100, 2)
        df = newDf.append(df)
        df.to_csv("{}{}.csv".format(data_realtime, stock), index=None)
        logger.info("Updated {}".format(stock))
        maVolume = getMAVolume(df)
        # if (maVolume >= 100000) and (maVolume <= df.Volume.iloc[0]):
        if (100000 <= df.Volume.iloc[0]) and (stock in high_value_stocks):
            ratio = round(df.iloc[0].Volume/df.iloc[1].Volume, 2)
            # print(ratio)
            if (not math.isinf(ratio)) and (((current_time >= "09:15") and (current_time <= "10:00") and (ratio >= 1)) or ((current_time >= "10:00") and (current_time <= "11:30") and (ratio >= 1.5)) or (ratio >= 2)):
                stocks.append(stock)
                ratios.append(ratio)
                currentVols.append(df.iloc[0].Volume)
                previousVols.append(df.iloc[1].Volume)
                closes.append(df.iloc[0].Close)
                lastCloses.append(df.iloc[1].Close)
                changes.append(round((df.iloc[0].Close - df.iloc[1].Close) / df.iloc[1].Close * 100, 2))
    highVolDf = pd.DataFrame.from_dict({
        "Stock": stocks,
        "Ratio": ratios,
        "Volume": currentVols,
        "YtdVolume": previousVols,
        "YtdPrice": lastCloses,
        "Price": closes,
        "Change": changes
    })
    highVolDf.sort_values("Ratio", ascending=False, inplace=True)
    highVolDf.to_csv(data_location + os.getenv("high_volumes"), index=False)

def updateStockActiveVolumes(s, startDate, endDate):
    url = "https://api4.fialda.com/api/services/app/StockInfo/GetTradingChartData?symbol={}&interval=1m&fromTime={}T08:45:00.000&toTime={}T15:00:00.000".format(s, startDate, endDate)
    rsGetRquest= requests.get(url)
    tradingData = rsGetRquest.json()['result']
    if (tradingData is None) or (len(tradingData) == 0):
        return []
    df = pd.DataFrame(tradingData)[['tradingTime', 'buyVolRatio', 'buyVol', 'sellVol']]
    df.tradingTime = df.tradingTime.str[:10]
    vol  = df.groupby(['tradingTime']).agg('sum')[['buyVol', 'sellVol']]
    volDict = [{"Date": startDate, "BuyVol": int(vol.buyVol[0]), "SellVol": int(vol.sellVol[0])}]
    df = pd.DataFrame(volDict)
    df['BuyVolRatio'] = int(round(df.BuyVol / (df.BuyVol + df.SellVol) * 100, 0))
    df = df[["Date", "BuyVolRatio", "BuyVol", "SellVol"]]
    # df.set_index("Date", inplace=True)
    return df

def updateActiveVolumes():
    stocks = getStocks(os.getenv('all_stocks'))
    volList = []
    date = getLastTradingDay()
    print("Extracting ratios on {}".format(date))
    # stocks = ["AAA"]
    for s in stocks:
        df = updateStockActiveVolumes(s, date, date)
        if len(df) > 0:
            # currentDf = pd.read_csv("data/active/{}.csv".format(s), index_col="Date")
            try:
                currentDf = pd.read_csv(data_location + "data/active/{}.csv".format(s))
                currentDf = currentDf[currentDf.Date != df.Date[0]]
                df = df.append(currentDf)
                df.to_csv(data_location + "data/active/{}.csv".format(s), index=None)
            except:
                logger.error("Error when updating ratio for {}".format(s))

def updateStockIntraday(date, stock):
    URL = "https://api4.fialda.com/api/services/app/Stock/GetIntraday?symbol={}".format(stock)
    rsGetRquest= requests.get(URL)
    tradingData = rsGetRquest.json()['result']
    if len(tradingData) == 0:
        return {}
    df = pd.DataFrame(tradingData)
    df = df[df.side != 'BS']
    df = df[["tradingTime","volume","price","side"]]
    df.to_csv(data_location + "data/intraday/{}/{}.csv".format(date, stock), index=None)

def updateIntradays():
    print("Update intradays")
    stocks = getStocks(os.getenv('all_stocks'))
    date = getLastTradingDay()
    try:
        os.mkdir(data_location + "data/intraday/{}".format(date)) 
    except:
        logger.info("Folder {} existed".format(date))
    for stock in stocks:
        updateStockIntraday(date, stock)

if __name__ == "__main__":
    (fromDate, toDate) = getDates()
    updatePriceAndVolume(fromDate, toDate)
    updateActiveVolumes()
    updateIntradays()
