from dotenv import load_dotenv
import pandas as pd
import logging
import logging.config
import os
from datetime import datetime
from common import readFile
from common import getCsvFiles

pd.options.mode.chained_assignment = None
logging.config.fileConfig(fname='log.conf', disable_existing_loggers=False)
logger = logging.getLogger()

load_dotenv(dotenv_path='stock.env')

data_location = os.getenv("data")
data_market = data_location + os.getenv('data_market')

LINK = 'https://s.cafef.vn/Lich-su-giao-dich-{}-1.chn'
RAW_NAME = ['Ngày', 'Giá đóng cửa', 'GD khớp lệnh',
            'Thay đổi (+/-%)', 'Giá mở cửa', 'Giá cao nhất', 'Giá thấp nhất']
NEW_NAME = ["Date", "Close", 'Volume',
            'Value', 'Change', "Open", "High", "Low"]
ORDERED = ['Close', 'Open', 'Change', 'High', 'Low', 'Volume']
FULL = ['Close', 'Open', 'High', 'Low', 'Change', 'Volume']


class Crawl:
    def __init__(self, mck, location):
        self.mck = mck
        self.link = LINK.format(self.mck)
        self.df_old, self.df_new = None, None
        self.location = location

    def getChange(self, change):
        start = change.index('(') + 1
        end = change.index('%') - 1
        return float(change[start:end])

    def clean(self, df):
        if df[3][0] == 'Giá bình quân':
            df.drop([3], axis=1, inplace=True)
            # https://stackoverflow.com/questions/42284617/reset-column-index-pandas
            df = df.T.reset_index(drop=True).T
        df.drop([4], axis=1, inplace=True)
        df.columns = df.iloc[0, :].values
        df = df.loc[2:, :][RAW_NAME]
        df.columns = NEW_NAME
        df["Date"] = pd.to_datetime(df["Date"], format='%d/%m/%Y')
        df.set_index("Date", inplace=True)
        df.Change = df.Change.apply(lambda x: self.getChange(x))
        for col in df.columns:
            df[col] = pd.to_numeric(df[col])
        df = df[ORDERED]
        return df

    def get_response(self):
        logger.info("Getting new data of {}".format(self.mck))
        df_new = pd.read_html(self.link, encoding='utf-8')[1]
        df_new = self.clean(df_new)
        logger.info("Completed getting new data of {}".format(self.mck))
        return df_new

    def merger_to_old_data(self):
        self.df_new = self.get_response()
        self.df_old = readFile(self.location + '{}.csv'.format(self.mck))
        df_gap = self.df_new.loc[:self.df_old.index.values[0], :][0:-1]
        df_gap = df_gap[FULL]
        logger.info("{} new records".format({len(df_gap)}))
        df = df_gap.append(self.df_old)
        return df

    def run(self):
        logger.info("Started updating {}".format(self.mck))
        df = self.merger_to_old_data()
        df.sort_index(ascending=True, inplace=True)
        df.sort_index(ascending=False, inplace=True)
        df.to_csv(self.location + '{}.csv'.format(self.mck))
        logger.info("Ended updating {}".format(self.mck))

def updateIntraday(location):
    today = datetime.today().strftime("%Y-%m-%d")
    logger.info("Started updating on {}".format(today))
    csvFiles = getCsvFiles(location)
    # csvFiles = ['VIB.csv']
    for i, csv in enumerate(csvFiles):
        try:
            logger.info((i, csv[0:3]))
            Crawl(csv[0:3], location).run()
        except Exception as e:
            logger.error(e)
    logger.info("Ended updating on {}".format(today))

if __name__ == '__main__':
    updateIntraday(data_market)