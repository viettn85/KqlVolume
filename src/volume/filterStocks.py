import sys
sys.path.append('src/crawler')
sys.path.append('src/util')

from dotenv import load_dotenv
import pandas as pd
import numpy as np
np.seterr(divide='ignore', invalid='ignore')

import logging
import logging.config
import os
from datetime import datetime
import pandas_ta as ta
from stockstats import StockDataFrame
from utils import *
from analysisVolume import *
from dailyCrawler import *
from ta.trend import ADXIndicator



load_dotenv(dotenv_path='stock.env')

results = 'data/market/results/'
filtered = 'data/market/intraday/'


def readFile(stock, location):
    df = pd.read_csv("{}{}.csv".format(location, stock))
    df.sort_values(by="date", ascending=False, inplace=True)
    df.rename(columns={'date': 'Date', 'close': 'Close', 'open': 'Open',
              'change': 'Change', 'high': 'High', 'low': 'Low', 'volume': 'Volume'}, inplace=True)
    df.set_index("Date", inplace=True)
    df = df.loc[:'2020-01-01']
    return df


def getIndicators(df):
    df.sort_index(inplace=True)
    # MACD
    df["exp1"] = df.Close.ewm(span=12, adjust=False).mean()
    df["exp2"] = df.Close.ewm(span=26, adjust=False).mean()
    df["MACD"] = df.exp1 - df.exp2
    df["MACD_SIGNAL"] = df.MACD.ewm(span=9, adjust=False).mean()
    df['Histogram'] = df.MACD - df.MACD_SIGNAL
    df.drop(['exp1', 'exp2'], axis=1, inplace=True)

    # RSI
    df['delta'] = df['Close'].diff()
    df["up"] = df.delta.clip(lower=0)
    df["down"] = -1 * df.delta.clip(upper=0)
    df["ema_up"] = df.up.ewm(com=13, adjust=False).mean()
    df["ema_down"] = df.down.ewm(com=13, adjust=False).mean()
    df["rs"] = df.ema_up/df.ema_down
    df['RSI'] = 100 - (100/(1 + df.rs))
    df.drop(['delta', 'up', 'down', 'ema_up',
            'ema_down', 'rs'], axis=1, inplace=True)

    # EMA200
    df['EMA200'] = df['Close'].ewm(
        span=200, min_periods=0, adjust=False, ignore_na=False).mean()

    # ADX
    adxI = ADXIndicator(high=df['High'], low=df['Low'],
                        close=df['Close'], window=14, fillna=False)
    df['PDI'] = round(adxI.adx_pos(), 2)
    df['NDI'] = round(adxI.adx_neg(), 2)
    df['ADX'] = round(adxI.adx(), 2)
    df.sort_index(ascending=False, inplace=True)


def filterStockByValues():
    stocks = list(pd.read_csv(os.getenv('all_stocks'), header=None)[0])
    # stocks = ["VPB"]
    highValueStocks = []
    values = []
    dataLocation = 'data_market'
    for stock in stocks:
        df = pd.read_csv("{}{}.csv".format(
            os.getenv(dataLocation), stock), parse_dates=['Date'], index_col=['Date'])
        df.sort_index(inplace=True)
        df["MA20"] = df.Volume.rolling(window=20).mean()
        df.sort_index(ascending=False, inplace=True)
        volumeMA20 = df.MA20[0]
        volume = df.Volume[0]
        price = df.Close[0]
        if (volumeMA20 * price / 1000000 > 6):
            highValueStocks.append(stock)
            values.append(round(volume * price / 1000000, 2))
    if len(highValueStocks) > 0:
        df = pd.DataFrame.from_dict(
            {"Stock": highValueStocks, "Value": values})
        df.sort_values("Value", ascending=False, inplace=True)
        df.to_csv(os.getenv("high_value_stocks"), header=None, index=None)
        # print(df.head(20))


def categorizeStocks():
    df = pd.read_csv(os.getenv('high_value_stocks'), header=None)
    df.columns = ['Stock', 'Value']
    df = df[df.Value > 8]
    stocks = list(df.Stock)
    # stocks = ['CTG', 'CTS', 'DRC', 'KDC']
    uptrends = []
    soft_zones = []
    ducky = []
    corrections = []
    missedEntry = []
    sideways = []
    bottoms = []
    if isCafefNotUpdated():
        dataLocation = 'data_realtime'
    else:
        dataLocation = 'data_market'
    for stock in stocks:
        # print(stock)
        df = pd.read_csv("{}{}.csv".format(
            os.getenv(dataLocation), stock), parse_dates=['Date'], index_col=['Date'])
        getIndicators(df)
        # print(df.head())
        # if df.Close[0] > df.EMA200[0]:
        if (df.Close[0] > df.EMA200[0]) or ((df.EMA200[0] - df.Close[0]) / df.EMA200[0] < 0.02):
            if (df.Histogram[0] > - 0.2) and (df.ADX[0] >= 20):
                # if ((df.Histogram[1] < 0.05) or (df.Histogram[2] < 0.05) or (df.Histogram[3] < 0.05)) and (df.RSI[0] > 40):
                if (df.Histogram[0] < 0) and (df.RSI[0] > 45) and (df.RSI[0] > df.RSI[1]):
                    ducky.append(stock)
                else:
                    recent = False
                    for i in range(0, 10):
                        if (df.Histogram[i] > 0) and (df.Histogram[i+1] < 0):
                            recent = True
                            break
                    if recent:
                        missedEntry.append(stock)
                    else:
                        uptrends.append(stock)
            else:
                corrections.append(stock)
        if abs(df.Close[0] - df.EMA200[0]) < 0.4:
            soft_zones.append(stock)
        price = df.Close[0]
        sideway = True
        for i in range(1, 10):
            if (abs(price - df.Close[i])/price >= 0.03) and (df.ADX[0] >= 16):
                sideway = False
        if sideway:
            sideways.append(stock)
        if (df.ADX[0] >= 16) and (df.PDI[0] >= df.PDI[1]) and (df.NDI[0] <= df.NDI[1]) and (df.ADX[0] > df.ADX[1]) and (df.ADX[1] <= df.ADX[2]):
            bottoms.append(stock)
    print(len(soft_zones))
    if len(uptrends) > 0:
        pd.DataFrame.from_dict({"Stock": uptrends}).to_csv(
            os.getenv('uptrend_stocks'), index=None, header=None)
    if len(missedEntry) > 0:
        pd.DataFrame.from_dict({"Stock": missedEntry}).to_csv(
            os.getenv('miss_entry_stocks'), index=None, header=None)
    if len(corrections) > 0:
        pd.DataFrame.from_dict({"Stock": corrections}).to_csv(
            os.getenv('correction_stocks'), index=None, header=None)
    if len(soft_zones) > 0:
        pd.DataFrame.from_dict({"Stock": soft_zones}).to_csv(
            os.getenv(os.getenv('soft_zone_stocks')), index=None, header=None)
    if len(ducky) > 0:
        pd.DataFrame.from_dict({"Stock": ducky}).to_csv(
            os.getenv('ducky_stocks'), index=None, header=None)
    if len(sideways) > 0:
        pd.DataFrame.from_dict({"Stock": sideways}).to_csv(
            os.getenv('sideway_stocks'), index=None, header=None)
    if len(bottoms) > 0:
        pd.DataFrame.from_dict({"Stock": bottoms}).to_csv(
            os.getenv('bottom_stocks'), index=None, header=None)
    if len(missedEntry) > 0 and len(soft_zones) > 0:
        potentialStocks = np.intersect1d(missedEntry, soft_zones)
        pd.DataFrame.from_dict({"Stock": potentialStocks}).to_csv(
            os.getenv('potential_stocks'), index=None, header=None)


def readCategory(stockList):
    try:
        df = pd.read_csv(os.getenv(stockList), header=None)
        if len(df) > 0:
            message = "<H2>{} {}</H2>".format(len(df),
                                              stockList.replace("_", " "))
            message = message + html_style_basic(df)
            return message
        return ""
    except:
        return ""


def sendCategories():
    lists = ["ducky_stocks", "potential_stocks", "miss_entry_stocks",
             "soft_zone_stocks", "sideway_stocks", 'bottom_stocks']
    message = ""
    for stockList in lists:
        # print(stockList)
        message = message + readCategory(stockList)
    sendEmail("Stock Categories", message, "html")


if __name__ == '__main__':
    data_market = os.getenv('data_market')
    updateIntraday(data_market)
    filterStockByValues()
    categorizeStocks()
    sendCategories()
    sendActiveVolList("ducky")
    sendActiveVolList("potential")
