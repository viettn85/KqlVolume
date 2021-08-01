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
from ta.trend import ADXIndicator
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
    weekday = datetime.now(timezone(tz)).weekday()
    if weekday < 5:
        currentTime = getCurrentTime()
        if (currentTime > "00:00") and (currentTime < "09:00"):
            if weekday > 0:
                return (datetime.now(timezone(tz)) + relativedelta(days=-1)).strftime(DATE_FORMAT)
            else:
                return getLastFriday().strftime(DATE_FORMAT)
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


def getIndicators(df):
    df.sort_index(ascending=False, inplace=True)
    
    # MACD
    df["exp1"] = df.Close.ewm(span=12, adjust=False).mean()
    df["exp2"] = df.Close.ewm(span=26, adjust=False).mean()
    df["MACD"] = df.exp1 - df.exp2
    df["MACD_SIGNAL"] = df.MACD.ewm(span=9, adjust=False).mean()
    df['Histogram'] = df.MACD - df.MACD_SIGNAL
    df.drop(['exp1', 'exp2'], axis=1, inplace=True)

    # RSI
    df['delta'] = df['Close'].diff()
    df["up"] = df.delta.clip(lower=0)
    df["down"] = -1 * df.delta.clip(upper=0)
    df["ema_up"] = df.up.ewm(com=13, adjust=False).mean()
    df["ema_down"] = df.down.ewm(com=13, adjust=False).mean()
    df["rs"] = df.ema_up/df.ema_down
    df['RSI'] = 100 - (100/(1 + df.rs))
    df.drop(['delta', 'up', 'down', 'ema_up',
            'ema_down', 'rs'], axis=1, inplace=True)

    # EMA200
    df['EMA200'] = df['Close'].ewm(
        span=200, min_periods=0, adjust=False, ignore_na=False).mean()
    # ADX
    adxI = ADXIndicator(high=df['High'], low=df['Low'],
                        close=df['Close'], window=14, fillna=False)
    df['PDI'] = round(adxI.adx_pos(), 2)
    df['NDI'] = round(adxI.adx_neg(), 2)
    df['ADX'] = round(adxI.adx(), 2)

    # MA
    df['MA20'] = df.Close.rolling(window=20).mean()
    df['MA50'] = df.Close.rolling(window=50).mean()
    df['MA200'] = df.Close.rolling(window=200).mean()

    df.sort_index(ascending=True, inplace=True)
    print(df.head())
