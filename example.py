#!/usr/bin/python3

from datetime import datetime, timedelta
from matplotlib.finance import quotes_historical_yahoo_ohlc as example
import matplotlib.finance as finance
from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import re
import sys


class Stock:

    def __init__(self, ticker):
        self.ticker = ticker


def make_soup(url):
    """
    @desc   - make a BeautifulSoup tree object for parsing
    @param  - url: the url destination to turn into soup
    @return - soup: the soup tree object
    """
    request = urlopen(url)
    raw_text = request.read()
    soup = BeautifulSoup(raw_text, "html.parser")
    return soup


def make_base_urls(soup, url):
    """
    @desc   - given a soup object taken from a yahoo finance quote page,
              generate a basic list url links to other metrics about
              the associated company
    @param  - soup: a BeautifulSoup soup object
    @param  - url: the base url from which links are created
    @return - urls: a dictionary of urls
    """
    urls = {}
    for link in soup.find_all("a"):
        try:
            suffix = link.get("href")
            if suffix.startswith("/quote") and ticker in suffix:
                new_url = re.sub("/quote/{}".format(ticker), suffix, url)
                match = re.findall("%s/(.*?)\?p=" % ticker, new_url)
                if match:
                    urls[match[0]] = new_url
        except AttributeError:
            continue
    return urls


def get_metrics(ticker):
    ticker = ticker.upper().strip()
    stock = Stock(ticker)
    url = "http://finance.yahoo.com/quote/{}".format(ticker)
    soup = make_soup(url)
    urls = make_base_urls(soup, url)

    stats = make_soup(urls["key-statistics"])

    # for link in stats.find_all("div", attrs={"data-test": "qsp-statistics"}): # class_=re.compile("^table")
    for link in stats.find_all("root"):
        print(link)
    stock.urls = urls
    return stock


def compound_annual_growth_rate(ticker, n=5):
    now = datetime.today() - timedelta(days=1)
    d1 = (now.year-n, now.month, now.day)
    d2 = (now.year, now.month, now.day)

    result = example(ticker.upper(), d1, d2)
    then_close = result[0][4]
    today_close = result[-1][4]
    cagr = ((today_close / then_close) ** (1/n)) - 1
    return cagr


def get_quote(ticker, n=5):
    ticker = ticker.upper().strip()
    now = datetime.today() - timedelta(days=1)
    d1 = (now.year-n, now.month, now.day)
    d2 = (now.year, now.month, now.day)
    fh = finance.fetch_historical_yahoo(ticker, d1, d2)
    # returns a file obj that has fields Date, Open, High, Low, Close, Volume, Adj Close
    return fh


if __name__ == "__main__":
    """
    tickers = sorted(["KO", "T", "CSCO", "BA", "MSFT", "AAPL", "NTT", "CVX", "INTC", "PG", "PNNT", "ABBV", "AFL",
                       "O", "TGT", "BBL", "CB", "CMI", "D", "DIS", "ES", "EXG", "F", "GD", "GILD", "GPS", "HP", "IBM",
                       "JNJ", "KMB", "LMT", "MAIN", "MCD", "MMM", "MO", "NEA", "NKE", "NOC", "OHI", "PFE", "QCOM", "RAI",
                       "RTN", "STAG", "TROW", "TRV", "UNP", "UPS", "VLO", "WBA", "WFC", "WMT", "XOM"])
    # large_caps = sorted(["CHL", "PG", "IBM", "KO", "SNY", "T", "TM", "TSM", "UL"])
     for ticker in tickers:
        rate = compound_annual_growth_rate(ticker)
        print("The 5-year compound annual growth rate of {ticker} is {:.2f}%".format(rate*100, ticker=ticker))
    """
    ticker = sys.argv[1].upper()
    periods = int(sys.argv[2])
    # rate = compound_annual_growth_rate(ticker, periods)
    # print("The {}-year compound annual growth rate of {ticker} is {:.2f}%".format(periods, rate * 100, ticker=ticker))
    result = get_metrics(ticker)
    # for key in result.urls:
    #   print(key, result.urls[key])
