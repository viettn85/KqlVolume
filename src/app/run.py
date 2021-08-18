import sys
sys.path.append('src/chart')
sys.path.append('src/crawler')
sys.path.append('src/volume')

from ducky import *
from intraday_hsc import *
from realtime import *
from analysisVolume import *

if __name__ == '__main__':
    # getIntraday(os.getenv("ps_symbol"))
    all_stocks = list(pd.read_csv(data_location + os.getenv('all_stocks'), header=None)[0])
    for stock in all_stocks:
        getIntraday(stock)
    updatePriceAndVolume()
    reportCashflows()
    exportList('portfolio')
    exportList('vn30')
    exportList('following')
    exportList('bottom')
    exportList('down')
