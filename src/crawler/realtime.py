import requests
import pandas as pd
import pytz
import os
from pytz import timezone
from datetime import datetime
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *
from dotenv import load_dotenv
import logging
import logging.config

load_dotenv(dotenv_path='stock.env')

data_location = os.getenv("data")
data_realtime = data_location + os.getenv('data_realtime')

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

def update(fromDate, toDate):
    startTime = getEpoch(fromDate )
    endTime = getEpoch(toDate)
    stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    for stock in stocks: 
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


def getEpoch(date):
    vntz = timezone('Asia/Ho_Chi_Minh')
    dateObj = datetime.strptime(date, '%Y-%m-%d')
    loc_dt = vntz.localize(dateObj)
    return (int)(loc_dt.timestamp())

def getDatetime(epoch):
    return datetime.fromtimestamp(epoch, tz= pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%dT%H:%M:%SZ')

def getDates():
    if datetime.now().weekday() < 5:
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() + relativedelta(days=-2)).strftime("%Y-%m-%d")
        return (yesterday, today)
    else:
        friday = (datetime.now() + relativedelta(weekday=FR(-1))).strftime("%Y-%m-%d")
        thursday = (datetime.now() + relativedelta(weekday=TH(-1))).strftime("%Y-%m-%d")
        return (thursday, friday)

if __name__ == "__main__":
    (fromDate, toDate) = getDates()
    update(fromDate, toDate)
