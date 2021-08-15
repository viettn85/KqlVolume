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

load_dotenv(dotenv_path='stock.env')

data_location = os.getenv("data")
data_realtime = data_location + os.getenv('data_realtime')
tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

def crawlStock(resolution, stock, startTime, endTime):
    URL = "https://chartdata1.mbs.com.vn/pbRltCharts/chart/history?symbol={}&resolution={}&from={}&to={}".format(stock, resolution, startTime, endTime)
    response = requests.get(URL)
    # print(response.json())
    dailyDf = pd.DataFrame(response.json())
    dailyDf['t']=dailyDf.apply(lambda x: getIntradayDatetime(x.t)[0:10] ,axis=1)
    dailyDf['Change'] = 0
    dailyDf.rename(columns={"t": "Date", "c": "Close", "o": "Open", "h": "High", "l": "Low", "Change": "Change", "v": "Volume"}, inplace=True)
    dailyDf = dailyDf[['Date', 'Close', 'Open', 'High', 'Low', 'Change', 'Volume']]
    dailyDf.Volume = dailyDf.Volume * 10
    dailyDf.Volume = dailyDf.Volume.astype(int)
    dailyDf.sort_values(by="Date", ascending=False, inplace=True)
    dailyDf['Close_Shift'] = dailyDf.Close.shift(-1)
    dailyDf.Change = dailyDf.apply(lambda x: round((x.Close - x.Close_Shift)/x.Close_Shift * 100, 2) ,axis=1)
    dailyDf.drop('Close_Shift', axis=1, inplace=True)
    dailyDf[['Close', 'Open', 'High', 'Low']] = round(dailyDf[['Close', 'Open', 'High', 'Low']], 2)
    if resolution == "D":
        dailyDf.to_csv("{}{}.csv".format(data_realtime, stock), index=None)
    else:
        dailyDf.to_csv("{}{}_{}.csv".format(data_realtime, stock, resolution), index=None)
    return dailyDf


def updatePriceAndVolume():
    try:
        fromDate = "2019-01-01"
        toDate = datetime.now(timezone(tz)).strftime(date_format)
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
        # all_stocks = ['VNINDEX']
        for stock in all_stocks: 
            try:
                dailyDf = crawlStock("D", stock, startTime, endTime)
                hourDf = crawlStock("60", stock, startTime, endTime)
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


if __name__ == "__main__":
    (fromDate, toDate) = getDates()
    updatePriceAndVolume()
    # updateActiveVolumes()
    # updateIntradays()
