#!/usr/bin/python3

from datetime import datetime, timedelta
from matplotlib.finance import quotes_historical_yahoo_ohlc as example
from bs4 import BeautifulSoup
from urllib.request import urlopen
import json
import re
import requests
import sys
import json


class Stock:
    """
    @desc   - a basic class to hold stock properties as objects.
    """
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


def get_statistics(ticker, periods=5):
    """
    @desc   - compile information about a stock from an online source.
              the stock data gathered can then be used to calculate various
              financial ratios
    @param  - ticker: the stock's ticker code
    @param  - periods: number of years to gather return data for
    @return - stock: a Stock class object containing many statistics
    """
    # make a soup object from yahoo finance page
    ticker = ticker.upper().strip()
    stock = Stock(ticker)
    url = "http://finance.yahoo.com/quote/{}".format(ticker)
    soup = make_soup(url)

    # get base urls with links to other information type pages
    urls = make_base_urls(soup, url)
    stock.urls = urls
    stock.annual_dividend = float(re.findall('"dividendRate":{"raw":(.*?),', soup.get_text())[0])

    # print(re.findall(".{100}1\.96", soup.get_text()))
    # you will get historical data here

    # gather other stats from this pre-created form
    params = {"formatted": "true",
              "crumb": "AKV/cl0TOgz",
              "lang": "en-US",
              "region": "US",
              "modules": "defaultKeyStatistics,financialData,calendarEvents",
              "corsDomain": "finance.yahoo.com"}
    url = "https://query1.finance.yahoo.com/v10/finance/quoteSummary/{}"
    r = requests.get(url.format(ticker), params=params)
    calendar_events = r.json()["quoteSummary"]["result"][0]["calendarEvents"]
    default_key_statistics = r.json()["quoteSummary"]["result"][0]["defaultKeyStatistics"]
    financial_data = r.json()["quoteSummary"]["result"][0]["financialData"]

    stock.book_value = default_key_statistics["bookValue"]["raw"]
    stock.price_to_book = default_key_statistics["priceToBook"]["raw"]
    stock.beta = default_key_statistics["beta"]["raw"]
    stock.forward_eps = default_key_statistics["forwardEps"]["raw"]
    stock.trailing_eps = default_key_statistics["trailingEps"]["raw"]
    stock.peg_ratio = default_key_statistics["pegRatio"]["raw"]
    stock.current_price = financial_data["currentPrice"]["raw"]
    stock.debt_to_equity = financial_data["debtToEquity"]["raw"]
    stock.free_cash_flow = financial_data["freeCashflow"]["raw"]
    stock.operating_cash_flow = financial_data["operatingCashflow"]["raw"]
    stock.dividend_yield = float(stock.annual_dividend / stock.current_price)
    stock.compound_annual_growth_rate = compound_annual_growth_rate(stock.ticker, periods)
    stock.periods = periods
    #for key in sorted(default_key_statistics.keys()):
    #    print(key, default_key_statistics[key])
    return stock


def get_historical_price_data(ticker, n):
    """
    @desc   - get historical high, low and close prices for a stock in a window of years.
              End date to gather data is always today.
    @param  - ticker: the stock whose data will be gathered
    @param  - n: an integer representing the number of years to gather data for
    @return - returns: list of daily returns in the format

                  [date, open, high, low, close, adj_close]
    """
    now = datetime.today() - timedelta(days=1)
    d1 = (now.year-n, now.month, now.day)
    d2 = (now.year, now.month, now.day)
    returns = example(ticker.upper(), d1, d2)
    return returns


def compound_annual_growth_rate(ticker, n=5):
    result = get_historical_price_data(ticker, n)
    then_close = result[0][4]
    today_close = result[-1][4]
    cagr = ((today_close / then_close) ** (1/n)) - 1
    return cagr


if __name__ == "__main__":
    ticker = sys.argv[1].upper().strip()
    result = get_statistics(ticker)
    print("the annual dividend for {} is ${} with a yield of {:.2f}%" .format(ticker, result.annual_dividend,
                                                                                  result.dividend_yield*100))
    print("The {}-year compound annual growth rate for {} is {:.2f}%".format(result.periods, result.ticker, result.compound_annual_growth_rate*100))