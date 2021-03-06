import sys
sys.path.insert(1, 'src/util')
import os
import sys
import pandas as pd
from datetime import datetime
import requests
import traceback
import json
import logging
import logging.config
from utils import *

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

from dotenv import load_dotenv
load_dotenv(dotenv_path='stock.env')
data_location = os.getenv("data")

PIN = os.getenv('pinf')
COOKIE = os.getenv('hsc_cookie')

date = getLastTradingDay()

def getIntraday(stock):
    location = data_location + "data/intraday/{}/".format(date)
    # print(location)
    try:
        if "VN30F" in stock:
            params = {
                "symbol": stock,
                "market": "VN",
                "time": -1,
                "workingDay": 0,
                "isLoadDynamic": False,
                "isLoadTransLog": True,
                "stockType": "F",
                "pageIndex": 0,
                "pageSize": 0,
                "coreType": -1
            }
            location = data_location + "data/future/transaction/{}/".format(stock)
        else:
            params = {
                "symbol": stock,
                "market": "O",
                "time": -1,
                "workingDay": 0,
                "isLoadDynamic": False,
                "isLoadTransLog": True,
                "stockType": "S",
                "pageIndex": 0,
                "pageSize": 0,
                "coreType": -1
            }
        headers = {
            'cookie': COOKIE,
            'Content-Type': 'application/json',
            'Content-Length': '1000',
            'Host': 'trading.hsc.com.vn'
            }
        r = requests.post(url=os.getenv('hsc_intraday_url'), headers=headers, data=json.dumps(params), verify=False).json()
        if 'result' not in r:
            logger.info("Request failed as authentication or incorrect input data for {}".format(stock))
        else:
            data = r['result']
            df = pd.DataFrame(data)
            df = df[['Time', 'Vol', 'TranType', 'Price']]
            df.Time = df.apply(lambda x: convertDateTime(x.Time), axis = 1)
            # df.Time = df.Time.str.slice(0, 9)
            df.Price = df.Price / 1000
            df.columns = ['DateTime', 'Volume', 'Side', 'Price']
            df.Side = df.apply(lambda x: convertSide(x.Side), axis=1)
            # print(df.head())
            if not os.path.isdir(location):
                os.mkdir(location)
            if len(df) > 0:
                if "VN30F" in stock:
                    df.to_csv("{}{}.csv".format(location, date), index=None)
                else:
                    df.to_csv("{}{}.csv".format(location, stock), index=None)
            logger.info("Updated transaction for {}".format(stock))
    except:
        traceback.print_exc()
        logger.error('Error to get intraday for {} on {}'.format(stock, date))

def convertDateTime(value):
    value = str(value)[0:-4].zfill(4)
    return "{}T{}:{}".format(date, value[:2], value[2:])

def convertSide(value):
    if value == 0:
        return ""
    elif value == 1:
        return "B"
    else:
        return "S"

if __name__ == "__main__":
    if len(sys.argv) == 1:
        all_stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
        # all_stocks = ['AAA']
        for stock in all_stocks:
            getIntraday(stock)
    elif sys.argv[1] == 'ps':
        getIntraday(os.getenv("ps_symbol"))
