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
import traceback
import time

load_dotenv(dotenv_path='stock.env')

data_location = os.getenv("data")
data_realtime = data_location + os.getenv('data_realtime')
tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

def crawlStock(resolution, stock, startTime, endTime):
    df = []
    count = 0
    while (len(df) == 0) and (count < 5):
        URL = "https://plus24.mbs.com.vn/tradingview/api/1.1/history?symbol={}&resolution={}&from={}&to={}".format(stock, resolution, startTime, endTime)
        # URL = "https://plus24.mbs.com.vn/tradingview/api/1.1/history?symbol={}&resolution={}&from={}&to={}".format(stock, resolution, startTime, endTime)
        # print(URL)
        # URL = "https://plus24.mbs.com.vn/tradingview/api/1.1/history?symbol=G36&resolution=60&from=1587679474&to=1629191854"
        response = requests.get(URL)
        # print(response.json())
        df = pd.DataFrame(response.json())
        count = count + 1
    if len(df) == 0:
        print("{} on {} has 0 record".format(stock. resolution))
    if resolution == 'D':
        df['t']=df.apply(lambda x: getIntradayDatetime(x.t)[0:10] ,axis=1)
    else:
        df['t']=df.apply(lambda x: getIntradayDatetime(x.t)[0:16] ,axis=1)
    df['Change'] = 0
    df.rename(columns={"t": "Date", "c": "Close", "o": "Open", "h": "High", "l": "Low", "Change": "Change", "v": "Volume"}, inplace=True)
    df = df[['Date', 'Close', 'Open', 'High', 'Low', 'Change', 'Volume']]
    df.Volume = df.Volume
    df.Volume = df.Volume.astype(int)
    df.sort_values(by="Date", ascending=False, inplace=True)
    df['Close_Shift'] = df.Close.shift(-1)
    df.Change = df.apply(lambda x: round((x.Close - x.Close_Shift)/x.Close_Shift * 100, 2) ,axis=1)
    df.drop('Close_Shift', axis=1, inplace=True)
    df[['Close', 'Open', 'High', 'Low']] = round(df[['Close', 'Open', 'High', 'Low']], 2)
    df.to_csv("{}{}_{}.csv".format(data_realtime, stock, resolution), index=None)
    return df


def updatePriceAndVolume():
    try:
        toDate = (datetime.now(timezone(tz)) + relativedelta(days=1)).strftime(date_format)
        fromDateDaily = (datetime.now(timezone(tz)) + relativedelta(months=-15)).strftime(date_format)
        fromDateHourly = (datetime.now(timezone(tz)) + relativedelta(months=-8)).strftime(date_format)
        startTimeDaily = getEpoch(fromDateDaily)
        startTimeHourly = getEpoch(fromDateHourly)
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
        # all_stocks = ['ACB']
        for stock in all_stocks: 
            try:
                dailyDf = crawlStock("D", stock, startTimeDaily, endTime)
                time.sleep(0.1)
                hourDf = crawlStock("60", stock, startTimeHourly, endTime)
                logger.info("Updated {}".format(stock))
                if (len(dailyDf) > 0) and (100000 <= dailyDf.Volume.iloc[0]) and (stock in high_value_stocks):
                    ratio = round(dailyDf.iloc[0].Volume/dailyDf.iloc[1].Volume, 2)
                    if (not math.isinf(ratio)) and (((current_time >= "09:15") and (current_time <= "10:00") and (ratio >= 1)) or ((current_time >= "10:00") and (current_time <= "11:30") and (ratio >= 1.5)) or (ratio >= 2)):
                        stocks.append(stock)
                        ratios.append(ratio)
                        currentVols.append(dailyDf.iloc[0].Volume)
                        previousVols.append(dailyDf.iloc[1].Volume)
                        closes.append(dailyDf.iloc[0].Close)
                        lastCloses.append(dailyDf.iloc[1].Close)
                        changes.append(round((dailyDf.iloc[0].Close - dailyDf.iloc[1].Close) / dailyDf.iloc[1].Close * 100, 2))
            except:
                logger.error("Error updating price and volume for {}".format(stock))
                # traceback.print_exc()
            time.sleep(0.1)
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
    except:
        logger.error("Error updating prices and volumes")
        traceback.print_exc()

if __name__ == "__main__":
    (fromDate, toDate) = getDates()
    updatePriceAndVolume()
    # updateActiveVolumes()
    # updateIntradays()
