import sys
sys.path.insert(1, 'src/util')
import requests
import pandas as pd
import operator
from datetime import datetime, date, timedelta


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
data_location = os.getenv("data")

def extractRatio(s, startDate, endDate):
    url = "https://api4.fialda.com/api/services/app/StockInfo/GetTradingChartData?symbol={}&interval=1d&fromTime={}T08:45:00.000&toTime={}T15:00:00.000".format(s, startDate, endDate)
    rsGetRquest= requests.get(url)
    tradingData = rsGetRquest.json()['result']
    if (tradingData is None) or (len(tradingData) == 0):
        return []
    df = pd.DataFrame(tradingData)[['tradingTime', 'buyVolRatio', 'buyVol', 'sellVol']]
    df.tradingTime = df.tradingTime.str[:10]
    df.buyVolRatio = df.buyVolRatio * 100
    df.rename(columns={"tradingTime": "Date", 'buyVolRatio': 'BuyVolRatio', "buyVol": "BuyVol", "sellVol": "SellVol"}, inplace=True)
    df[["BuyVolRatio", "BuyVol", "SellVol"]] = df[["BuyVolRatio", "BuyVol", "SellVol"]].fillna(0.0).astype(int)
    df.set_index("Date", inplace=True)
    print(s, len(df))
    return df

def extractRealtimeRatio(s, startDate, endDate):
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

def extractHourlyRatio(s):
    date = getLastTradingDay()
    url = "https://api4.fialda.com/api/services/app/StockInfo/GetTradingChartData?symbol={}&interval=1m&fromTime={}T08:45:00.000&toTime={}T15:00:00.000".format(s, date, date)
    rsGetRquest= requests.get(url)
    tradingData = rsGetRquest.json()['result']
    if (tradingData is None) or (len(tradingData) == 0):
        return []
    df = pd.DataFrame(tradingData)[['tradingTime', 'buyVolRatio', 'buyVol', 'sellVol']]
    df.tradingTime = df.tradingTime.str[:13]
    vol  = df.groupby(['tradingTime']).agg('sum')[['buyVol', 'sellVol']]
    print(vol)

def extractRatios():
    if datetime.now().weekday() >= 5:
        return
    stocks = getStocks(os.getenv('all_stocks'))
    volList = []
    date = getLastTradingDay()
    print("Extracting ratios on {}".format(date))
    # stocks = ["AAA"]
    for s in stocks:
        df = extractRealtimeRatio(s, date, date)
        if len(df) > 0:
            # currentDf = pd.read_csv("data/active/{}.csv".format(s), index_col="Date")
            try:
                currentDf = pd.read_csv(data_location + "data/active/{}.csv".format(s))
                currentDf = currentDf[currentDf.Date != df.Date[0]]
                df = df.append(currentDf)
                df.to_csv(data_location + "data/active/{}.csv".format(s), index=None)
            except:
                a = 0
    
def extractHistoricalRatios(stocks):
    endDate = datetime.now()
    startDate = endDate + relativedelta(months=-1)
    for s in stocks:
        volList = []
        df = extractRatio(s, startDate.strftime(DATE_FORMAT), endDate.strftime(DATE_FORMAT))
        df.to_csv(data_location + "data/active/{}.csv".format(s))

def showRatios(s):
    try:
        print(pd.read_csv(data_location + "data/active/{}.csv".format(s), index_col = "Date"))
    except:
        print(extractRealtimeRatio(s, today, today))
        endDate = datetime.now()
        startDate = endDate + relativedelta(months=-1)
        print(extractRatio(s, startDate.strftime(DATE_FORMAT), endDate.strftime(DATE_FORMAT)))

def getHighRatios():
    stocks = getStocks(os.getenv('high_value_stocks'))
    portfolioStocks = getStocks(os.getenv('portfolio'))
    targetStocks = getStocks(os.getenv('target'))
    highRatioStocks = []
    highBuyVols = []
    high = []
    all = []
    portfolio = []
    target = []
    message = ""
    dataLocation = 'data_market'
    for s in stocks:
        try:
            df = pd.read_csv(data_location + "data/active/{}.csv".format(s), index_col = "Date")
            row = 0
            if s in portfolioStocks:
                portfolio.append({"Stock": s, "BuyVolRatio": df.BuyVolRatio[row], "BuyVol": df.BuyVol[row], "SellVol": df.SellVol[row]})
            if not isSideway(s, dataLocation):
                continue
            all.append({"Stock": s, "BuyVolRatio": df.BuyVolRatio[row], "BuyVol": df.BuyVol[row], "SellVol": df.SellVol[row]})
            if s in targetStocks:
                target.append({"Stock": s, "BuyVolRatio": df.BuyVolRatio[row], "BuyVol": df.BuyVol[row], "SellVol": df.SellVol[row]})
            if (df.BuyVolRatio[row] > 60) and (df.BuyVolRatio[row + 1] > 50):
                highRatioStocks.append({"Stock": s, "BuyVolRatio": df.BuyVolRatio[row], "BuyVol": df.BuyVol[row], "SellVol": df.SellVol[row]})
            if (df.BuyVol[row + 1] * 1.5 <= df.BuyVol[row]) and (df.BuyVolRatio[row] > 50):
                highBuyVols.append({"Stock": s, "BuyVolRatio": df.BuyVolRatio[row], "BuyVol": df.BuyVol[row], "SellVol": df.SellVol[row]})
            if (df.BuyVol[row + 1] * 1.5 <= df.BuyVol[row]) and (df.BuyVolRatio[0] > 50) and (df.BuyVolRatio[row + 1] > 50):
                high.append({"Stock": s, "BuyVolRatio": df.BuyVolRatio[row], "BuyVol": df.BuyVol[row], "SellVol": df.SellVol[row]})
        except:
            aa = ""
    lastCashflow = getLastCashflow()
    reportDf = pd.read_csv(lastCashflow, index_col='Stock')

    if len(portfolio) > 0:
        message = message + "<H2>Portfolio ratios :</H2>\n"
        message = message + joinTradeVol(reportDf, portfolio, "portfolio") + "\n\n"

    if len(target) > 0:
        message = message + "<H2>Target ratios :</H2>\n"
        message = message + joinTradeVol(reportDf, target, "target") + "\n\n"
    if len(high) > 0:
        message = message + "<H2>Active Buy Vols increased 50% and Ratios > 50% last two days :</H2>\n"
        message = message + joinTradeVol(reportDf, high, "high") + "\n\n"

    if len(highBuyVols) > 0:
        message = message + "<H2>Active Buy Vols increased 50%:</H2>\n"
        message = message + joinTradeVol(reportDf, highBuyVols, "high_vol") + "\n\n"

    if len(highRatioStocks) > 0:
        message = message + "<H2>Ratios > 50% last two days:</H2>\n"
        message = message + joinTradeVol(reportDf, highRatioStocks, "high_ratios") + "\n\n"
    
    if len(all) > 0:
        message = message + "<H2>Top 10 highest ratios :</H2>\n"
        message = message + joinTradeVol(reportDf, all, "all") + "\n\n"
    return message

def joinTradeVol(reportDf, highList, filename):
    highDf = pd.DataFrame(highList)
    highDf.set_index("Stock", inplace=True)
    finalDf = pd.merge(highDf, reportDf, on="Stock")
    if filename == "portfolio":
        finalDf.sort_values(["BuyVolRatio", "SellVol"], inplace=True)
        finalDf = finalDf[["BuyVolRatio", "BuyVol", "SellVol", "G", "BG"]]
        return html_style_basic(finalDf)
    if filename == "target":
        finalDf.sort_values(["BuyVolRatio", "BuyVol"], ascending=False, inplace=True)
        return html_style_basic(finalDf)
    if filename == "all":
        finalDf = finalDf[finalDf.B >= 300]
        finalDf.sort_values("BuyVolRatio", ascending = False, inplace=True)
        return html_style_basic(finalDf.head(10))
    finalDf = finalDf[(finalDf.G >= int(os.getenv('gap'))) & (finalDf.B >= int(os.getenv('buy')))]
    finalDf.to_csv(data_location + "data/active/{}.csv".format(filename))
    return html_style_basic(finalDf)

def getIntradays():
    print("Update intradays")
    stocks = getStocks(os.getenv('all_stocks'))
    date = datetime.now().strftime(DATE_FORMAT)
    try:
        os.mkdir(data_location + "data/intraday/{}".format(date)) 
    except:
        logger.info("Folder {} existed".format(date))
    for stock in stocks:
        getIntraday(date, stock)

def getIntraday(date, stock):
    URL = "https://api4.fialda.com/api/services/app/Stock/GetIntraday?symbol={}".format(stock)
    rsGetRquest= requests.get(URL)
    tradingData = rsGetRquest.json()['result']
    if len(tradingData) == 0:
        return {}
    df = pd.DataFrame(tradingData)
    df = df[df.side != 'BS']
    df = df[["tradingTime","volume","price","side"]]
    df.to_csv(data_location + "data/intraday/{}/{}.csv".format(date, stock), index=None)

def reportHourVolumes(stock):
    date = getLastTradingDay()
    highValueDf = pd.read_csv(data_location + os.getenv('high_value_stocks'), header=None)
    highValueDf.columns = ['Stock', 'Value']
    highValueDf.set_index('Stock', inplace=True)
    try: 
        all_df = pd.read_csv(data_location + "data/intraday/{}/{}.csv".format(date, stock), parse_dates=['tradingTime'])
        all_df['Hour'] = all_df.tradingTime.dt.hour
        tradeCounts = []
        bigTradeCounts = []
        for hour in [9, 10, 11, 13, 14]:
            df = all_df.loc[all_df['tradingTime'].dt.hour == hour]
            sideDict  = df.groupby(['side']).agg('count')['price'].to_dict()
            sideDict['Hour'] = hour
            tradeCounts.append(sideDict)
            df['Value'] = df.volume * df.price
            print(df.head())
            print(df.price.iloc[0], test)
            if (df.price.iloc[0] <= 30) or (highValueDf.loc[stock].Value <= 300):
                df = df[df.Value > 500000]
            else:
                df = df[df.Value > 1000000]
            sideDict  = df.groupby(['side']).agg('count')['price'].to_dict()
            sideDict['Hour'] = hour
            bigTradeCounts.append(sideDict)
        tradeCounts = pd.DataFrame(tradeCounts)
        bigTradeCounts = pd.DataFrame(bigTradeCounts)
        bigTradeCounts.rename(columns={"B": "BB", "S": "BS"}, inplace=True)
        finalDf = pd.merge(tradeCounts, bigTradeCounts, on="Hour")
        finalDf.fillna(0, inplace=True)
        finalDf["G"] = finalDf.B - finalDf.S
        finalDf["BG"] = finalDf.BB - finalDf.BS
        finalDf = finalDf[["Hour", "B", "S", "G", "BB", "BS", "BG"]]
        print(finalDf)
    except:
        print("Error to report {} ".format(stock))
        traceback.print_exc()
    
    
def reportCashflows():
    stocks = getStocks(os.getenv('high_value_stocks'))
    highValueDf = pd.read_csv(data_location + os.getenv('high_value_stocks'), header=None)
    highValueDf.columns = ['Stock', 'Value']
    highValueDf.set_index('Stock', inplace=True)
    date = getLastTradingDay()
    print("Report cash flows on {}".format(date))
    tradeCounts = []
    bigTradeCounts = []
    # stocks = ['AAA', 'TCH', 'HBC', 'DRC', 'MWG']
    for stock in stocks:
        try: 
            df = pd.read_csv(data_location + "data/intraday/{}/{}.csv".format(date, stock))
            sideDict  = df.groupby(['side']).agg('count')['price'].to_dict()
            sideDict['Stock'] = stock
            tradeCounts.append(sideDict)
            df['Value'] = df.volume * df.price
            if (highValueDf.loc[stock].Value <= 300) or (df.price[0] <= 30):
                df = df[df.Value > 500000]
            else:
                df = df[df.Value > 1000000]
            sideDict  = df.groupby(['side']).agg('count')['price'].to_dict()
            sideDict['Stock'] = stock
            bigTradeCounts.append(sideDict)
        except:
            print("Error to report {} ".format(stock))
            # traceback.print_exc()
    tradeCounts = pd.DataFrame(tradeCounts)
    bigTradeCounts = pd.DataFrame(bigTradeCounts)
    bigTradeCounts.rename(columns={"B": "BB", "S": "BS"}, inplace=True)
    finalDf = pd.merge(tradeCounts, bigTradeCounts, on="Stock")
    finalDf.fillna(0, inplace=True)
    finalDf["G"] = finalDf.B - finalDf.S
    finalDf["BG"] = finalDf.BB - finalDf.BS
    finalDf = finalDf[["Stock", "B", "S", "G", "BB", "BS", "BG"]]
    finalDf.to_csv(data_location + "data/cashflow/{}.csv".format(date), index=None)
    # print(finalDf)

def analyzeActiveVol(stockList):
    df = pd.DataFrame()
    highActiveDf = pd.DataFrame()
    highVolDf = pd.DataFrame()
    try:
        stocks = list(pd.read_csv(data_location + "data/stock/{}.csv".format(stockList), header=None)[0])
        for stock in stocks:
            try:
                stockDf = pd.read_csv(data_location + "data/active/{}.csv".format(stock))
                stockDf['Stock'] = stock
                df = df.append(stockDf[0:1])
                if (stockDf.BuyVolRatio[0] > 50) and (stockDf.BuyVolRatio[1] > 50):
                    highActiveDf = highActiveDf.append(stockDf[0:1])
                if (stockDf.BuyVolRatio[0] > 50) and (stockDf.BuyVol[0] >= stockDf.BuyVol[1] * 1.5):
                    highVolDf = highVolDf.append(stockDf[0:1])
            except:
                print()
        df = sortActiveDf(df, stockList)
        if len(highActiveDf) > 0:
            highActiveDf = sortActiveDf(highActiveDf, stockList)
        if len(highVolDf) > 0:
            highVolDf = sortActiveDf(highVolDf, stockList)
    except:
        a = 0
    return (df, highActiveDf, highVolDf)

def sendActiveVolList(stockList):
    (df, highActiveDf, highVolDf) = analyzeActiveVol(stockList)
    message = ""
    if len(highActiveDf) > 0:
        message = message + "<H2>{} {}</H2>".format(len(highActiveDf), " stocks having buy vol ratios > 50% on two days\n")
        message = message + html_style_basic(highActiveDf)
    if len(highVolDf) > 0:
        message = message + "<H2>{} {}</H2>".format(len(highVolDf), " stocks having abnormal high buy vol\n")
        message = message + html_style_basic(highVolDf)
    if message != "":
        sendEmail(stockList.capitalize()  + " stock report", message, "html")

def showActiveVol(stockList):
    (df, highActiveDf, highVolDf) = analyzeActiveVol(stockList)
    print("High active list:")
    print(highActiveDf)
    print("High abnormal buy vol:")
    print(highVolDf)
    print("All list:")
    print(df)

def sortActiveDf(activeDf, stockList):
    activeDf.drop(["Date"], axis = 1, inplace=True)
    activeDf = activeDf[["Stock", "BuyVolRatio", "BuyVol", "SellVol"]]
    if stockList == "vn30":
        activeDf.sort_values(["BuyVolRatio", "BuyVol"], ascending=False, inplace=True)
    elif stockList == "portfolio":
        activeDf.sort_values(["BuyVolRatio", "BuyVol"], inplace=True)
    else:
        activeDf.sort_values(["BuyVol", "BuyVolRatio"], ascending=False, inplace=True)
    return activeDf

def analyzeCashflow(action, stockList):
    lastCashflow = getLastCashflow()
    df = pd.read_csv(lastCashflow, index_col='Stock')
    if (action == "B10"):
        df.sort_values("G", ascending=False, inplace=True)
        print(df.head(10))
    elif (action == "S10"):
        df.sort_values("G", inplace=True)
        print(df.head(10))
    elif (action == "BB10"):
        df.sort_values("BG", ascending=False, inplace=True)
        print(df.head(10))
    elif (action == "BS10"):
        df.sort_values("BG", inplace=True)
        print(df.head(10))
    elif (action == "list"):
        if ("," in stockList) or (len(stockList) == 3):
            stocks = stockList.split(',')
        else:
            stocks = list(pd.read_csv(data_location + "data/stock/{}.csv".format(stockList), header=None)[0])
        df = df[df.index.isin(stocks)]
        df.sort_values(["BG", "G"], ascending=False, inplace=True)
        print(df)
    else:
        action = action.split(',')
        df = df[df.index.isin(action)]
        print(df)

def sendCashflowReports():
    lastCashflow = getLastCashflow()
    df = pd.read_csv(lastCashflow, index_col='Stock')
    message = ""

    message = message +  "<H2>Portfolio:</H2> \n"
    portfolioDf = df[df.index.isin(getStocks(os.getenv('portfolio')))]
    portfolioDf = portfolioDf[["BG", "BB", "BS", "G", "B", "S"]]
    portfolioDf.sort_values(['BG', 'G'], inplace=True)
    message = message + html_style_basic(portfolioDf) + "\n\n"

    message = message +  "<H2>Target:</H2> \n"
    targetDf = df[df.index.isin(getStocks(os.getenv('target')))]
    message = message + html_style_basic(targetDf) + "\n\n"

    message = message +  "<H2>Top Big BUY Trade Counts:</H2> \n"
    df.sort_values("BG", ascending=False, inplace=True)
    message = message + html_style_basic(df.head(10)) + "\n\n"

    message = message + "<H2>Top BUY Trade Counts:</H2> \n"
    df.sort_values("G", ascending=False, inplace=True)
    message = message + html_style_basic(df.head(10)) + "\n\n"
    
    
    message = message +  "<H2>Top Big SELL Trade Counts:</H2> \n"
    df.sort_values("BG", inplace=True)
    message = message + html_style_basic(df.head(10)) + "\n\n"

    message = message +  "<H2>Top SELL Trade Counts:</H2> \n"
    df.sort_values("G", inplace=True)
    message = message + html_style_basic(df.head(10)) + "\n\n"

    sendEmail("Cashflow reports", message, "html")

def autoScan():
    getIntradays()
    reportCashflows()
    sendCashflowReports()
    extractRatios()
    sendEmail("High ratio reports", getHighRatios(), "html")

if __name__ == '__main__':
    if (sys.argv[1] == 'active'):
        stocks = getStocks(os.getenv('high_value_stocks'))
        if (len(sys.argv) == 2):
            print("Crawling")
            extractHistoricalRatios(stocks)
        else:
            if (sys.argv[2] == "update"):
                extractRatios()
            elif (sys.argv[2] == "high"):
                print(getHighRatios())
            else:
                showRatios(sys.argv[2])
    if (sys.argv[1] == 'scan'):
        showActiveVol(sys.argv[2])
    if (sys.argv[1] == 'intraday'):
        print("Intraday")
        getIntradays()
    if (sys.argv[1] == 'sides'):
        reportCashflows()
    if (sys.argv[1] == 'cash'):
        stockList = ""
        if (len(sys.argv) == 4):
            stockList = sys.argv[3]
        print(stockList)
        analyzeCashflow(sys.argv[2], stockList)
    if (sys.argv[1] == 'auto'):
        autoScan()
    if (sys.argv[1] == 'hour'):
        # extractHourlyRatio(sys.argv[2])
        reportHourVolumes(sys.argv[2])
    # if (sys.argv[1] == 'hour'):
