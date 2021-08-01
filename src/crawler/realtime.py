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
tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

def update(fromDate, toDate):
    startTime = getEpoch(fromDate )
    endTime = getEpoch(toDate)
    all_stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    stocks = []
    ratios = []
    currentVols = []
    previousVols = []
    lastCloses = []
    closes = []
    changes = []
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
        if df.iloc[0].Volume >= 100000:
            ratio = round(df.iloc[0].Volume/df.iloc[1].Volume, 2)
            # print(ratio)
            if ((current_time >= "02:15") and (current_time <= "03:00") and (ratio >= 1)) or ((current_time >= "03:00") and (current_time <= "04:30") and (ratio >= 1.5)) or ((current_time >= "14:00") and (current_time <= "15:00") and (ratio >= 1.5)) or (ratio >= 2):
                stocks.append(stock)
                ratios.append(ratio)
                currentVols.append(df.iloc[0].Volume)
                previousVols.append(df.iloc[1].Volume)
                closes.append(df.iloc[0].Close)
                lastCloses.append(df.iloc[1].Close)
                changes.append(round((df.iloc[0].Close - df.iloc[1].Close), 2))
    highVolDf = pd.DataFrame.from_dict({
        "Stock": stocks,
        "Ratio": ratios,
        "Current": currentVols,
        "Previous": previousVols,
        "Last_Close": lastCloses,
        "Close": closes,
        "Change": changes
    })
    highVolDf.sort_values("Ratio", ascending=False, inplace=True)
    print(highVolDf)
    highVolDf.to_csv(data_location + "data/high_volumes.csv", index=False)

def getEpoch(date):
    vntz = timezone(tz)
    dateObj = datetime.strptime(date, date_format)
    loc_dt = vntz.localize(dateObj)
    return (int)(loc_dt.timestamp())

def getDatetime(epoch):
    return datetime.fromtimestamp(epoch, tz= pytz.timezone('Asia/Bangkok')).strftime(datetime_format)

def getDates():
    if datetime.now().weekday() < 5:
        today = datetime.now().strftime(date_format)
        yesterday = (datetime.now() + relativedelta(days=-2)).strftime(date_format)
        return (yesterday, today)
    else:
        friday = (datetime.now() + relativedelta(weekday=FR(-1))).strftime(date_format)
        thursday = (datetime.now() + relativedelta(weekday=TH(-1))).strftime(date_format)
        return (thursday, friday)

if __name__ == "__main__":
    # (fromDate, toDate) = getDates()
    # update(fromDate, toDate)

    # Current time in UTC
    now_utc = datetime.now(timezone(tz))
    print(datetime.now())
    print(now_utc.strftime(datetime_format))
    print(now_utc.weekday())

    # Convert to Asia/Kolkata time zone
    now_asia = now_utc.astimezone(timezone('Asia/Kolkata'))
    print(now_asia.strftime(datetime_format))
