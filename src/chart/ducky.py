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


def draw(stock, location, timeframe):
    try:
        df = pd.read_csv("{}{}_{}.csv".format(data_realtime, stock, timeframe), parse_dates=True)
        price = df.iloc[0].Close
        getIndicators(df)
        df.index = pd.DatetimeIndex(df['Date'])
        df['ADX20'] = 20
        df['RSI70'] = 70
        df['RSI30'] = 30
        df['Stoch20'] = 20
        df['Stoch80'] = 80
        df['MACD0'] = 0
        df = df[0:150]
        df.sort_index(ascending=True, inplace=True)
        
        
        mc = fplt.make_marketcolors(
                                up='tab:blue',down='tab:red',
                                volume='inherit',
        )
        apds = [ fplt.make_addplot(df['MA20'], panel=0,color='red'),
                    fplt.make_addplot(df['MA50'], panel=0,color='blue'),
                    fplt.make_addplot(df['MA200'], panel=0,color='green'),
                    fplt.make_addplot(df['Volume'], type = 'line', linestyle=' ', panel =1, mav = 20, color='g'),
                    fplt.make_addplot(df['MACD'], panel=2,color='blue'),
                    fplt.make_addplot(df['MACD_SIGNAL'], panel=2,color='red'),
                    fplt.make_addplot(df['MACD0'], panel=2,color='grey'),
                    fplt.make_addplot(df['%K'], panel=3, color='red'),
                    fplt.make_addplot(df['%D'], panel=3,color='blue'),
                    fplt.make_addplot(df['Stoch20'], panel=3,color='grey'),
                    fplt.make_addplot(df['Stoch80'], panel=3,color='grey'),
                    fplt.make_addplot(df['RSI'], panel=4,color='red'),
                    fplt.make_addplot(df['RSI70'], panel=4,color='grey'),
                    fplt.make_addplot(df['RSI30'], panel=4,color='grey'),
                    fplt.make_addplot(df['ADX'], panel=5,color='blue'),
                    fplt.make_addplot(df['PDI'], panel=5,color='green'),
                    fplt.make_addplot(df['NDI'], panel=5,color='red'),
                    fplt.make_addplot(df.ADX20, type = 'line', panel=5,color='grey')
                    ]
        # s  = fplt.make_mpf_style(base_mpl_style="seaborn", y_on_right=True, marketcolors=mc, mavcolors=["red","orange","skyblue"])
        s  = fplt.make_mpf_style(base_mpl_style="seaborn", y_on_right=True, marketcolors=mc)
        fplt.plot(
                    df,
                    type='candle',
                    style=s,
                    title="{} - {} - {}".format(stock, timeframe, price),
                    ylabel='',
                    # mav=(20, 50, 200),
                    volume=True,
                    addplot=apds,
                    savefig=dict(fname='{}/{}_{}.png'.format(location, stock, timeframe),dpi=100,pad_inches=0.25)
        )
    except:
        print("Error to export {}".format(stock))
        traceback.print_exc()

def exportAll():
    stocks = list(pd.read_csv("stocks/{}.csv".format('all_stocks'), header=None)[0])
    for stock in stocks:
        draw(stock, os.getenv("images") + "daily", 'D')
        draw(stock, os.getenv("images") + 'hourly', '60')
    print("Exported all daily and hourly charts")

def exportList(stockList):
    try:
        stocks = list(pd.read_csv("stocks/{}.csv".format(stockList), header=None)[0])
        # stocks = ['ELC']
        location = os.getenv("images") + stockList
        for stock in stocks:
            draw(stock, location, 'D')
            draw(stock, location, '60')
        print("Exported " + stockList)
    except:
        print("Error to export {}".format(stockList))
        # traceback.print_exc()

def exportCustom(stocks, stockList):
    location = os.getenv("images") + stockList
    for stock in stocks:
        draw(stock, location, 'D')
        draw(stock, location, '60')
    print("Exported " + stockList)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        if sys.argv[1] == "all":
            exportAll()
        else:
            exportList(sys.argv[1])
    if len(sys.argv) == 3:
        if (',' in sys.argv[1]) or (len(sys.argv[1]) == 3):
            stocks = sys.argv[1].split(',')
            exportCustom(stocks, sys.argv[2])
