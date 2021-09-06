import sys, os
sys.path.append('src/util')
import pandas as pd
import numpy as np
import mplfinance as fplt
from utils import *
from dotenv import load_dotenv
import shutil
import traceback

load_dotenv(dotenv_path='stock.env')
np.seterr(divide='ignore', invalid='ignore')
data_location = os.getenv("data")
data_realtime = data_location + os.getenv("data_realtime")

duration = 2

def findAllBottoms(stockList):
    try:
        stocks = list(pd.read_csv("stocks/{}.csv".format(stockList), header=None)[0])
        for stock in stocks:
            findBottom(stock, "60")
    except:
        print("Error to searching {}".format(stockList))

def findBottom(stock, timeframe):
    df = pd.read_csv("{}{}_{}.csv".format(data_realtime, stock, timeframe), parse_dates=True)
    getIndicators(df)
    if len(df) > 500:
        last = 500
    else:
        last = len(df) - 1
    print("{} on chart {} from {}".format(stock, timeframe, df.Date.iloc[last]))
    for i in range(0, last):
        # if isLongAtBottom(df, i):
        #     print("Long at Bottom at {} - {}".format(df.Date.iloc[i], verify(df, i, 'L')))
        if isLongADXBottom(df, i):
            print("Long at ADX Bottom at {}: {}".format(df.Date.iloc[i], verify(df, i, 'L')))
        if isShortADXBottom(df, i):
            print("Short at ADX Bottom at {}: {}".format(df.Date.iloc[i], verify(df, i, 'L')))
        if isLongUpTrend(df, i):
            print("LONG MA at {}: {}".format(df.Date.iloc[i], verify(df, i, 'L')))
        if isShortDownTrend(df, i):
            print("SHORT MA at {}: {}".format(df.Date.iloc[i], verify(df, i, 'S')))

def isMACDBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return (row.Histogram > prow.Histogram) and (row.MACD_SIGNAL < 0) and (row.MACD < 0)

def isMACDTop(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return (row.Histogram < prow.Histogram) and (row.MACD_SIGNAL > 0) and (row.MACD > 0)

def isMACDIncreasing(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return (row.Histogram > prow.Histogram)

def isMACDDecreasing(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return (row.Histogram < prow.Histogram)

def isAdxBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    minADX = min(list(df.loc[rowIndex:rowIndex+duration].ADX))
    return (row.ADX > prow.ADX) and (row.ADX > minADX) and (df.iloc[rowIndex + duration].ADX > minADX)\
        and (df.iloc[rowIndex + duration].ADX < df.iloc[rowIndex + duration + 1].ADX)

def isAdxTop(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    maxADX = max(list(df.loc[rowIndex:rowIndex+duration].ADX))
    return (row.ADX < prow.ADX) and (row.ADX < maxADX) and (df.iloc[rowIndex + 5].ADX < maxADX)

def isDIReverse(df, rowIndex, up, down):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    maxUp = max(list(df.loc[rowIndex:rowIndex+duration][up]))
    minDown = min(list(df.loc[rowIndex:rowIndex+duration][down]))
    return (row[up] < prow[up]) and (row[up] < maxUp) and (df.iloc[rowIndex + 5][up] < maxUp)\
        and (row[down] > prow[down]) and (row[down] > minDown) and (df.iloc[rowIndex + duration][down] > minDown)\
            and (row.ADX > 25) and (row[up] > row[down])

def isDiTop(df, rowIndex):
    return isDIReverse(df, rowIndex, 'PDI', 'NDI')

def isDiBottom(df, rowIndex):
    return isDIReverse(df, rowIndex, 'NDI', 'PDI')

def isChance(df, rowIndex, up, down):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 5]
    return isAdxBottom(df, rowIndex) and (row[up] > prow[up]) and (row[down] < prow[down]) and (row[up] > row[down]) and (prow[up] < prow[down])

def isLong(df, rowIndex):
    # return isChance(df, rowIndex, 'PDI', 'NDI')
    row = df.iloc[rowIndex]
    return isAdxBottom(df, rowIndex) and isMACDIncreasing(df, rowIndex) and (row.PDI > row.NDI)

def isShort(df, rowIndex):
    # return isChance(df, rowIndex, 'NDI', 'PDI')
    row = df.iloc[rowIndex]
    return isAdxBottom(df, rowIndex) and isMACDDecreasing(df, rowIndex) and (row.PDI < row.NDI)

def getTrend(upDf, date):
    subDf = upDf[upDf.Date < date]
    if subDf.iloc[0].MA200 > subDf.iloc[0].Close:
        return "Downtrend"
    else:
        return "Uptrend"

def isUptrend(df, rowIndex):
    row = df.iloc[rowIndex]
    return (row.MA200 < min(row.MA50, row.MA20)) and (row.Close > row.MA200)

def isDowntrend(df, rowIndex):
    row = df.iloc[rowIndex]
    return (row.MA200 > max(row.MA50, row.MA20)) and (row.Close < row.MA200)

def isLongADXBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    maxMA = max(row.MA200, row.MA50, row.MA20)
    return isAdxBottom(df, rowIndex) and isUptrend(df, rowIndex) and (row.Close > maxMA)

def isShortADXBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    minMA = min(row.MA200, row.MA50, row.MA20)
    return isAdxBottom(df, rowIndex) and isDowntrend(df, rowIndex) and (row.Close < minMA)

def isLongAtBottom(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    return isDiBottom(df, rowIndex) and (row.MA200 > row.MA50) and (row.MA50 > row.MA20) and (row.MA20 > row.Close) and (row.ADX <= prow.ADX)

def isLongUpTrend(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    isAboveMA200 = (row.Close > row.MA200) and (row.MA200 > prow.MA200)
    isMAIncreasing = (row.MA50 > prow.MA50) or (row.MA20 > prow.MA20)
    isHistogramIncreasing = row.Histogram > prow.Histogram
    maxMA = max(row.MA20, row.MA50, row.MA200)
    isPriceIncreasing = (row.Close > maxMA) and ((row.Open < maxMA) or (min(prow.Close, prow.Open) < maxMA))
    return isAboveMA200 and isMAIncreasing and isHistogramIncreasing and isPriceIncreasing

def isShortDownTrend(df, rowIndex):
    row = df.iloc[rowIndex]
    prow = df.iloc[rowIndex + 1]
    
    isBelowMA200 = (row.Close < row.MA200) and (row.MA200 < prow.MA200)
    isMADecreasing = (row.MA50 < prow.MA50) or (row.MA20 < prow.MA20)
    isHistogramDecreasing = (row.Histogram < prow.Histogram) or (row.MACD_SIGNAL < prow.MACD_SIGNAL)
    minMA = min(row.MA20, row.MA50, row.MA200)
    isPriceDecreasing = (row.Close < minMA) and ((row.Open > minMA) or (max(prow.Close, prow.Open) > minMA))
    # if row.Date == '2021-08-20T09:50:00Z':
    #     print(row.Close, row.MA200, row.MA50, row.MA20, row.Histogram)
    #     print(isBelowMA200, isMADecreasing, isHistogramDecreasing, isPriceDecreasing)
    
    return isBelowMA200 and isMADecreasing and isHistogramDecreasing and isPriceDecreasing

def verify(df, rowIndex, trade):
    row = df.iloc[rowIndex]
    entryPrice = (row.Low + row.Close) / 2
    checkIndex = rowIndex-10
    if trade == 'L':
        return max(list(df.loc[checkIndex:rowIndex-2].High)) - entryPrice
    elif trade == 'S':
        return entryPrice - min(list(df.loc[checkIndex:rowIndex-2].Low))
    else:
        return False

if __name__ == "__main__":
    findBottom("GVR", "D")
