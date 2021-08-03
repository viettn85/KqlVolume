import sys, os
sys.path.append('src/util')
import pandas as pd
import mplfinance as fplt
from utils import *
from dotenv import load_dotenv
load_dotenv(dotenv_path='stock.env')

data_location = os.getenv("data")
data_market = data_location + os.getenv("data_realtime")

def draw(stock):
    df = pd.read_csv("{}{}.csv".format(data_market, stock), index_col="Date", parse_dates=True)[0:300]
    getIndicators(df)
    print(df.head())
    df.sort_index(ascending=True, inplace=True)
    
    
    mc = fplt.make_marketcolors(
                            up='tab:blue',down='tab:red',
                            # edge='lime',
                            # wick={'up':'blue','down':'red'},
                            volume='inherit',
    )
    apds = [ fplt.make_addplot(df['Volume'], type = 'line', linestyle=' ', panel =1, mav = 20, color='g'),
                fplt.make_addplot(df['RSI'], panel=4,color='g',ylabel='RSI'),
                fplt.make_addplot(df['ADX'], panel=3,color='blue'),
                fplt.make_addplot(df['PDI'], panel=3,color='green'),
                fplt.make_addplot(df['NDI'], panel=3,color='red'),
                fplt.make_addplot(df['MACD'], panel=2,color='r'),
                fplt.make_addplot(df['MACD_SIGNAL'], panel=2,color='g')
                ]
    s  = fplt.make_mpf_style(base_mpl_style="seaborn",  y_on_right=True, marketcolors=mc, mavcolors=["red","orange","skyblue"])
    fplt.plot(
                df,
                type='candle',
                style=s,
                title=stock,
                # ylabel='Price',
                mav=(20, 50, 200),
                volume=True,
                addplot=apds
                # savefig=dict(fname='{}.png'.format(stock),dpi=100,pad_inches=0.25)
    )

import cufflinks as cf
import chart_studio.plotly as py

cf.set_config_file(theme='pearl',sharing='public',offline=True)
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
# import cufflinks as cf
# init_notebook_mode()


def drawQuant(stock):
    df = pd.read_csv("{}{}.csv".format(data_market, stock), index_col="Date", parse_dates=True)[0:300]
    # df.sort_index(ascending=True, inplace=True)
    qf=cf.QuantFig(df,title='Apple Quant Figure',legend='top',name='GS', asImage=True, display_image=True)
    qf.add_bollinger_bands()
    qf.add_volume()
    # qf.iplot(asImage=True)
    py.image.save_as(qf.iplot(), 'scatter_plot', format='png')

if __name__ == "__main__":
    # drawQuant("AAA")
    draw("MWG")
