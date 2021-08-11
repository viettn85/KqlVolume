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
        # all_stocks = ['VND']
        for stock in all_stocks: 
            try:
                URL = "https://chartdata1.mbs.com.vn/pbRltCharts/chart/history?symbol={}&resolution=D&from={}&to={}".format(stock, startTime, endTime)
                response = requests.get(URL)
                # print(response.json())
                newDf = pd.DataFrame(response.json())
                newDf['t']=newDf.apply(lambda x: getIntradayDatetime(x.t)[0:10] ,axis=1)
                newDf['Change'] = 0
                newDf.rename(columns={"t": "Date", "c": "Close", "o": "Open", "h": "High", "l": "Low", "Change": "Change", "v": "Volume"}, inplace=True)
                newDf = newDf[['Date', 'Close', 'Open', 'High', 'Low', 'Change', 'Volume']]
                newDf.Volume = newDf.Volume * 10
                newDf.Volume = newDf.Volume.astype(int)
                newDf.sort_values(by="Date", ascending=False, inplace=True)
                newDf['Close_Shift'] = newDf.Close.shift(-1)
                newDf.Change = newDf.apply(lambda x: round((x.Close - x.Close_Shift)/x.Close_Shift * 100, 2) ,axis=1)
                newDf.drop('Close_Shift', axis=1, inplace=True)
                newDf[['Close', 'Open', 'High', 'Low']] = round(newDf[['Close', 'Open', 'High', 'Low']], 2)
                newDf.to_csv("{}{}.csv".format(data_realtime, stock), index=None)
                logger.info("Updated {}".format(stock))
                maVolume = getMAVolume(newDf)
                # if (maVolume >= 100000) and (maVolume <= df.Volume.iloc[0]):
                if (len(newDf) > 0) and (100000 <= newDf.Volume.iloc[0]) and (stock in high_value_stocks):
                    ratio = round(newDf.iloc[0].Volume/newDf.iloc[1].Volume, 2)
                    if (not math.isinf(ratio)) and (((current_time >= "09:15") and (current_time <= "10:00") and (ratio >= 1)) or ((current_time >= "10:00") and (current_time <= "11:30") and (ratio >= 1.5)) or (ratio >= 2)):
                        stocks.append(stock)
                        ratios.append(ratio)
                        currentVols.append(newDf.iloc[0].Volume)
                        previousVols.append(newDf.iloc[1].Volume)
                        closes.append(newDf.iloc[0].Close)
                        lastCloses.append(newDf.iloc[1].Close)
                        changes.append(round((newDf.iloc[0].Close - newDf.iloc[1].Close) / newDf.iloc[1].Close * 100, 2))
            except:
                logger.error("Error updating price and volume for {}".format(stock))
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
