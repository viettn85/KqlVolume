from datetime import datetime
import pandas as pd
import email, smtplib, ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import traceback, os, logging, glob
from pytz import timezone
from datetime import datetime
from dateutil.relativedelta import *

import logging.config
logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

from dotenv import load_dotenv
load_dotenv(dotenv_path='stock.env')

tz = os.getenv("timezone")
date_format = os.getenv("date_format")
datetime_format = os.getenv("datetime_format")

DATE_FORMAT = "%Y-%m-%d"
data_location = os.getenv("data")

def getMAVolume(df):
    df.sort_values(['Date'], inplace=True)
    df['MA'] = df.Volume.rolling(window=20).mean()
    df.sort_values(['Date'], ascending=False, inplace=True)
    maVolume = df.MA.iloc[0]
    df.drop('MA', axis=1, inplace=True)
    return maVolume

def isSideway(stock, dataLocation):
    df = pd.read_csv("{}{}.csv".format(data_location + os.getenv(dataLocation), stock), parse_dates=['Date'], index_col=['Date'])
    sideway = True
    price = df.Close[0]
    for i in range(1, 3):
        if abs(price - df.Close[i])/price >= 0.05:
            sideway = False
            break
    return sideway

def isCafefNotUpdated():
    now = datetime.now(timezone(tz))
    currentTime = str(now.strftime("%H:%M"))
    return (now.weekday() < 5) and (currentTime > "09:15") and (currentTime < "20:30")

def isTradingTime():
    now = datetime.now(timezone(tz))
    currentTime = str(now.strftime("%H:%M"))
    return (now.weekday() < 5) and (currentTime > "09:15") and (currentTime < "15:00")

def isATO():
    now = datetime.now(timezone(tz))
    currentTime = str(now.strftime("%H:%M"))
    return (now.weekday() < 5) and (currentTime > "09:00") and (currentTime < "09:15")

def isATC():
    now = datetime.now(timezone(tz))
    currentTime = str(now.strftime("%H:%M"))
    return (now.weekday() < 5) and (currentTime > "14:30") and (currentTime < "14:45")

def getLastTradingDay():
    if datetime.now(timezone(tz)).weekday() < 5:
        currentTime = getCurrentTime()
        if (currentTime > "00:00") and (currentTime < "09:00"):
            return (datetime.now(timezone(tz)) + relativedelta(days=-1)).strftime(DATE_FORMAT)
        else:
            return datetime.now(timezone(tz)
    ).strftime(DATE_FORMAT)
    else:
        return getLastFriday().strftime(DATE_FORMAT)

def getLastFriday():
    return datetime.now(timezone(tz)) + relativedelta(weekday=FR(-1))

def getCurrentTime():
    now = datetime.now(timezone(tz))
    return str(now.strftime("%H:%M"))

def getStocks(stockFile):
    return list(pd.read_csv(data_location + stockFile, header=None)[0])

def getLastCashflow():
    list_of_files = glob.glob(data_location + os.getenv("data_cashflow") + "*") # * means all if need specific format then *.csv
    latest_file = max(list_of_files, key=os.path.getmtime)
    print(latest_file)
    return latest_file

def sendEmail(subject, text, style):
    now = datetime.now(timezone(tz))
    current_time = now.strftime("%Y-%m-%d %H-%M")
    try:
        subject = "{} - {}".format(subject, current_time)
        body = text
        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["Subject"] = subject
        # Add body to email
        message.attach(MIMEText(body, style))
        # message.attach(qualifiedPrices)
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(os.getenv('sender'), os.getenv('password'))
            server.sendmail(os.getenv('sender'), os.getenv('receiver').split(','), message.as_string())
        logger.info("Sent {}".format(subject))
    except:
        logger.error("Failed to send email to notify qualified stocks {}".format(current_time))
        traceback.print_exc()

def html_style_basic(df,index=True):
    x = df.to_html(index = index)
    x = x.replace('<table border="1" class="dataframe">','<table style="border-collapse: collapse; border-spacing: 0; width: 25%;">')
    x = x.replace('<th>','<th style="text-align: right; padding: 5px; border-left: 1px solid #cdd0d4;" align="left">')
    x = x.replace('<td>','<td style="text-align: right; padding: 5px; border-left: 1px solid #cdd0d4; border-right: 1px solid #cdd0d4;" align="left">')
    x = x.replace('<tr style="text-align: right;">','<tr>')

    x = x.split()
    count = 2 
    index = 0
    for i in x:
        if '<tr>' in i:
            count+=1
            if count%2==0:
                x[index] = x[index].replace('<tr>','<tr style="background-color: #f2f2f2;" bgcolor="#f2f2f2">')
        index += 1
    return ' '.join(x)


def getEpoch(date):
    vntz = timezone(tz)
    dateObj = datetime.strptime(date, date_format)
    loc_dt = vntz.localize(dateObj)
    return (int)(loc_dt.timestamp())

def getDatetime(epoch):
    return datetime.fromtimestamp(epoch, tz= timezone('Asia/Bangkok')).strftime(datetime_format)

def getDates():
    if datetime.now().weekday() < 5:
        today = datetime.now().strftime(date_format)
        yesterday = (datetime.now() + relativedelta(days=-2)).strftime(date_format)
        return (yesterday, today)
    else:
        friday = (datetime.now() + relativedelta(weekday=FR(-1))).strftime(date_format)
        thursday = (datetime.now() + relativedelta(weekday=TH(-1))).strftime(date_format)
        return (thursday, friday)