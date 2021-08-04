import sys, os
sys.path.append('src/util')
import pandas as pd
import numpy as np
import mplfinance as fplt
from utils import *
from dotenv import load_dotenv
import shutil

load_dotenv(dotenv_path='stock.env')
np.seterr(divide='ignore', invalid='ignore')
data_location = os.getenv("data")
data_realtime = data_location + os.getenv("data_realtime")

def draw(stock, location):
    df = pd.read_csv("{}{}.csv".format(data_realtime, stock), parse_dates=True)[0:300]
    getIndicators(df)
    df.index = pd.DatetimeIndex(df['Date'])
    df['ADX20'] = 20
    df.sort_index(ascending=True, inplace=True)
    
    
    mc = fplt.make_marketcolors(
                            up='tab:blue',down='tab:red',
                            volume='inherit',
    )
    apds = [ fplt.make_addplot(df['Volume'], type = 'line', linestyle=' ', panel =1, mav = 20, color='g'),
                fplt.make_addplot(df['RSI'], panel=4,color='g',ylabel='RSI'),
                fplt.make_addplot(df['ADX'], panel=3,color='blue'),
                fplt.make_addplot(df['PDI'], panel=3,color='green'),
                fplt.make_addplot(df['NDI'], panel=3,color='red'),
                fplt.make_addplot(df.ADX20, type = 'line', panel=3,color='grey'),
                fplt.make_addplot(df['MACD'], panel=2,color='r'),
                fplt.make_addplot(df['MACD_SIGNAL'], panel=2,color='g')
                ]
    s  = fplt.make_mpf_style(base_mpl_style="seaborn",  y_on_right=True, marketcolors=mc, mavcolors=["red","orange","skyblue"])
    fplt.plot(
                df,
                type='candle',
                style=s,
                title=stock,
                ylabel='',
                mav=(20, 50, 200),
                volume=True,
                addplot=apds,
                savefig=dict(fname='{}/{}.png'.format(location, stock),dpi=100,pad_inches=0.25)
    )

import cufflinks as cf
import chart_studio.plotly as py

cf.set_config_file(theme='pearl',sharing='public',offline=True)
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
# import cufflinks as cf
# init_notebook_mode()

def exportList(stockList, location=None):
    print("Exporting " + stockList)
    stocks = list(pd.read_csv(data_location + os.getenv(stockList), header=None)[0])
    if location == None:
        location = os.getenv("images") + stockList
    else:
        location = os.getenv("images") + location
    print(location)
    if os.path.isdir(location):
        shutil.rmtree(location, ignore_errors=True)
    os.mkdir(location) 
    for stock in stocks:
        draw(stock, location)
    print("Exported " + stockList)

def drawQuant(stock):
    df = pd.read_csv("{}{}.csv".format(data_realtime, stock), index_col="Date", parse_dates=True)[0:300]
    # df.sort_index(ascending=True, inplace=True)
    qf=cf.QuantFig(df,title='Apple Quant Figure',legend='top',name='GS', asImage=True, display_image=True)
    qf.add_bollinger_bands()
    qf.add_volume()
    # qf.iplot(asImage=True)
    py.image.save_as(qf.iplot(), 'scatter_plot', format='png')

if __name__ == "__main__":
    if sys.argv[1] == "daily":
        exportList("all_stocks", "daily")
    elif sys.argv[1] in ['ducky', 'following']:
        exportList(sys.argv[1])
