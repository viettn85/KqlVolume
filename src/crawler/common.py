import os
import pandas as pd


def readFile(f):
    def dateParser(x): return pd.datetime.strptime(x, "%Y-%m-%d")
    df = pd.read_csv(f, parse_dates=True, index_col="Date",
                     date_parser=dateParser)
    # df = pd.read_csv(f, parse_dates=True, index_col="Date")
    return df


def getCsvFiles(location):
    try:
        entries = os.listdir(location)
        return list(filter(lambda x: os.path.splitext(x)[1], entries))
    except:
        print("Something wrong with file location: {}".format(location))
