import sys, os
sys.path.append('src/util')
import pandas as pd
import numpy as np
import mplfinance as fplt
from utils import *
from dotenv import load_dotenv
import shutil
import traceback

load_dotenv(dotenv_path='future.env')
np.seterr(divide='ignore', invalid='ignore')
data_location = os.getenv("data")
data_realtime = data_location + os.getenv("data_realtime")

duration = 2

def isMACDBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return (row.Histogram > prow.Histogram) and (row.MACD_SIGNAL < 0) and (row.MACD < 0)

def isMACDTop(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return (row.Histogram < prow.Histogram) and (row.MACD_SIGNAL > 0) and (row.MACD > 0)

def isIncreasing(df, rowIndex, field):
    for i in range(3):
        if df.iloc[rowIndex + i][field] < df.iloc[rowIndex + i + 1][field]:
            return False
    return True

def isDecreasing(df, rowIndex, field):
    for i in range(3):
        if df.iloc[rowIndex + i][field] > df.iloc[rowIndex + i + 1][field]:
            return False
    return True

def isTop(df, rowIndex, field):
    row = df.iloc[rowIndex]
    prow1 = df.iloc[rowIndex + 1]
    prow2 = df.iloc[rowIndex + 2]
    threshold = True
    if field in ('ADX', 'PDI', 'NDI'):
        threshold = prow1[field] > 30
    return (prow2[field] < prow1[field]) and (row[field] < prow1[field]) and isIncreasing(df, rowIndex + 2, field) and threshold


def isBottom(df, rowIndex, field):
    row = df.iloc[rowIndex]
    prow1 = df.iloc[rowIndex + 1]
    prow2 = df.iloc[rowIndex + 2]
    return (prow2[field] > prow1[field]) and (row[field] > prow1[field]) and isDecreasing(df, rowIndex + 2, field)

def isDIReverse(df, rowIndex, up, down):
    row = df.iloc[rowIndex]
    # prow = df.iloc[rowIndex + 1]
    # maxUp = max(list(df.loc[rowIndex:rowIndex+duration][up]))
    # minDown = min(list(df.loc[rowIndex:rowIndex+duration][down]))
    # return (row[up] < prow[up]) and (row[up] < maxUp) and (df.iloc[rowIndex + 5][up] < maxUp)\
    #     and (row[down] > prow[down]) and (row[down] > minDown) and (df.iloc[rowIndex + duration][down] > minDown)\
    #         and (row.ADX > 25) and (row[up] > row[down])
    return isTop(df, rowIndex, up) and isBottom(df, rowIndex, down) and (row[up] > row[down])

def isDiTop(df, rowIndex):
    return isDIReverse(df, rowIndex, 'PDI', 'NDI')

def isDiBottom(df, rowIndex):
    return isDIReverse(df, rowIndex, 'NDI', 'PDI')

def isUptrend(df, rowIndex):
    row = df.iloc[rowIndex]
    return (row.MA200 < min(row.MA50, row.MA20)) and (row.Close > row.MA200)

def isDowntrend(df, rowIndex):
    row = df.iloc[rowIndex]
    return (row.MA200 > max(row.MA50, row.MA20)) and (row.Close < row.MA200)

def isLongADXBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    maxMA = max(row.MA200, row.MA50, row.MA20)
    return isBottom(df, rowIndex, 'ADX') and isUptrend(df, rowIndex) and (row.Close > maxMA) and (row.MACD_SIGNAL > prow.MACD_SIGNAL)

def isShortADXBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    minMA = min(row.MA200, row.MA50, row.MA20)
    return isBottom(df, rowIndex, 'ADX') and isDowntrend(df, rowIndex) and (row.Close < minMA) and (row.MACD_SIGNAL < prow.MACD_SIGNAL)

def isLongAtBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return isDiBottom(df, rowIndex) and (row.MA200 > row.MA50) and (row.MA50 > row.MA20) and (row.MA20 > row.Close) and (row.ADX <= prow.ADX)

def isLongUpTrend(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    isAboveMA200 = (row.Close > row.MA200) and (row.MA200 > prow.MA200)
    isMAIncreasing = (row.MA50 > prow.MA50) or (row.MA20 > prow.MA20)
    isHistogramIncreasing = (row.Histogram > 0) and (row.Histogram > prow.Histogram)
    maxMA = max(row.MA20, row.MA50, row.MA200)
    isPriceIncreasing = (row.Close > maxMA) and (row.Open < maxMA)
    return isAboveMA200 and isMAIncreasing and isHistogramIncreasing and isPriceIncreasing

def isShortDownTrend(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    isBelowMA200 = (row.Close < row.MA200) and (row.MA200 < prow.MA200)
    isMADecreasing = (row.MA50 < prow.MA50) or (row.MA20 < prow.MA20)
    isHistogramDecreasing = (row.Histogram < 0) and (row.Histogram < prow.Histogram)
    minMA = min(row.MA20, row.MA50, row.MA200)
    isPriceDecreasing = (row.Close < minMA) and (row.Open > minMA)    
    return isBelowMA200 and isMADecreasing and isHistogramDecreasing and isPriceDecreasing

def verify(df, rowIndex, trade):
    row = df.iloc[rowIndex]
    entryPrice = (row.Low + row.Close) / 2
    checkIndex = rowIndex-10
    if rowIndex < 10:
        return True
    if trade == 'L':
        return max(list(df.loc[checkIndex:rowIndex-2].High)) - entryPrice
    elif trade == 'S':
        return entryPrice - min(list(df.loc[checkIndex:rowIndex-2].Low))
    else:
        return False

def isTrending(df, rowIndex, field):
    return df.iloc[rowIndex][field] > max(list(df.loc[rowIndex+1:rowIndex+20][field]))

def warn(stocks, timeframes):
    bottomStocks = []
    adx = []
    pdi = []
    ndi = []
    for stock in stocks:
        for timeframe in timeframes:
            rowIndex = 5
            df = pd.read_csv("{}{}_{}.csv".format(data_realtime, stock, timeframe), parse_dates=True)
            getIndicators(df)
            if isDiBottom(df, rowIndex):
                bottomStocks.append(stock)
            if isTrending(df, rowIndex, 'ADX'):
                adx.append(stock)
            if isTrending(df, rowIndex, 'PDI'):
                pdi.append(stock)
            if isTrending(df, rowIndex, 'NDI'):
                ndi.append(stock)
    if len(bottomStocks) > 0:
        print("Bottom::", ",".join(bottomStocks))
    if len(adx) > 0:
        print("ADX::", ",".join(adx))
    if len(pdi) > 0:
        print("PDI::", ",".join(pdi))
    if len(ndi) > 0:
        print("NDI::", ",".join(ndi))

def scan(stocks, timeframes):
    matchedStocks = []
    matchedTimeframes = []
    matchedDateTime = []
    matchedActions = []
    for stock in stocks:
        for timeframe in timeframes:
            rowIndex = 0
            df = pd.read_csv("{}{}_{}.csv".format(data_realtime, stock, timeframe), parse_dates=True)
            getIndicators(df)
            if isLongADXBottom(df, rowIndex):
                matchedStocks.append(stock)
                matchedTimeframes.append(timeframe)
                matchedDateTime.append(df.iloc[rowIndex].Date)
                matchedActions.append("Long ADX Bottom")
            if isShortADXBottom(df, rowIndex):
                matchedStocks.append(stock)
                matchedTimeframes.append(timeframe)
                matchedDateTime.append(df.iloc[rowIndex].Date)
                matchedActions.append("Short ADX Bottom")
            if isLongUpTrend(df, rowIndex):
                matchedStocks.append(stock)
                matchedTimeframes.append(timeframe)
                matchedDateTime.append(df.iloc[rowIndex].Date)
                matchedActions.append("Long MA")
            if isShortDownTrend(df, rowIndex):
                matchedStocks.append(stock)
                matchedTimeframes.append(timeframe)
                matchedDateTime.append(df.iloc[rowIndex].Date)
                matchedActions.append("Short MA")

    df = pd.DataFrame.from_dict({
        "Stock": matchedStocks,
        "Timeframe": matchedTimeframes,
        "Datetime": matchedDateTime,
        "Action": matchedActions
        })
    if len(df) > 0:
        print(df)
        print(",".join(np.unique(list(df.Stock))))
        # sendEmail("PS Actions", html_style_basic(df), "html")
    else:
        print("No special action")

def scanHistory(stocks, timeframes):
    matchedStocks = []
    matchedTimeframes = []
    matchedDateTime = []
    matchedActions = []
    for stock in stocks:
        for timeframe in timeframes:
            for rowIndex in range(10):
                df = pd.read_csv("{}{}_{}.csv".format(data_realtime, stock, timeframe), parse_dates=True)
                getIndicators(df)
                if isLongADXBottom(df, rowIndex):
                    matchedStocks.append(stock)
                    matchedTimeframes.append(timeframe)
                    matchedDateTime.append(df.iloc[rowIndex].Date)
                    matchedActions.append("Long ADX Bottom")
                if isShortADXBottom(df, rowIndex):
                    matchedStocks.append(stock)
                    matchedTimeframes.append(timeframe)
                    matchedDateTime.append(df.iloc[rowIndex].Date)
                    matchedActions.append("Short ADX Bottom")
                if isLongUpTrend(df, rowIndex):
                    matchedStocks.append(stock)
                    matchedTimeframes.append(timeframe)
                    matchedDateTime.append(df.iloc[rowIndex].Date)
                    matchedActions.append("Long MA")
                if isShortDownTrend(df, rowIndex):
                    matchedStocks.append(stock)
                    matchedTimeframes.append(timeframe)
                    matchedDateTime.append(df.iloc[rowIndex].Date)
                    matchedActions.append("Short MA")

    df = pd.DataFrame.from_dict({
        "Stock": matchedStocks,
        "Timeframe": matchedTimeframes,
        "Datetime": matchedDateTime,
        "Action": matchedActions
        })
    if len(df) > 0:
        print(df)
    else:
        print("No special action")

if __name__ == "__main__":
    stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    timeframes = ['60', 'D']
    if len(sys.argv) == 1:
        scan(stocks, timeframes)
    elif sys.argv[1] == 'history':
        scanHistory(stocks, timeframes)
    elif sys.argv[1] == 'warn':
        warn(stocks, timeframes)
