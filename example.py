#!/usr/bin/python3

from matplotlib.finance import *
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.request import urlopen
import operator
import re
import requests
import sys


class Stock:
    """
    @desc   - a basic class to hold stock properties as objects.
    """
    def __init__(self, ticker_symbol):
        self.ticker = ticker_symbol


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


def get_statistics(ticker_symbol, time_periods=5):
    """
    @desc   - compile information about a stock from an online source.
              the stock data gathered can then be used to calculate various
              financial ratios
    @param  - ticker_symbol: the stock's ticker code
    @param  - time_periods: number of years to gather return data for
    @return - stock: a Stock class object containing many statistics
    """
    # make a soup object from yahoo finance page
    ticker_symbol = ticker_symbol.upper().strip()
    stock = Stock(ticker_symbol)
    url = "http://finance.yahoo.com/quote/{}".format(ticker_symbol)
    soup = make_soup(url)

    # get base urls with links to other information type pages
    urls = make_base_urls(soup, url)
    stock.urls = urls
    profile = make_soup(stock.urls["profile"])

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
    r = requests.get(url.format(ticker_symbol), params=params)
    calendar_events = r.json()["quoteSummary"]["result"][0]["calendarEvents"]
    default_key_statistics = r.json()["quoteSummary"]["result"][0]["defaultKeyStatistics"]
    financial_data = r.json()["quoteSummary"]["result"][0]["financialData"]

    # stock.book_value = default_key_statistics["bookValue"]["raw"] # missing 'raw' field
    # stock.price_to_book = default_key_statistics["priceToBook"]["raw"] # missing 'raw' field
    # stock.beta = default_key_statistics["beta"]["raw"] # missing 'raw' field
    # stock.forward_eps = default_key_statistics["forwardEps"]["raw"]
    # stock.trailing_eps = default_key_statistics["trailingEps"]["raw"]
    # stock.peg_ratio = default_key_statistics["pegRatio"]["raw"] # missing 'raw' field
    stock.current_price = financial_data["currentPrice"]["raw"]
    # stock.debt_to_equity = financial_data["debtToEquity"]["raw"]
    # stock.free_cash_flow = financial_data["freeCashflow"]["raw"]
    # stock.operating_cash_flow = financial_data["operatingCashflow"]["raw"]
    try:
        stock.annual_dividend = float(re.findall('"dividendRate":{"raw":(.*?),', soup.get_text())[0])
        stock.dividend_yield = float(stock.annual_dividend / stock.current_price)
    except IndexError:
        stock.annual_dividend = 0.0
        stock.dividend_yield = 0.0
    stock.compound_annual_growth_rate = compound_annual_growth_rate(stock.ticker, time_periods)
    stock.dividend_history = get_dividend_history(stock.ticker, time_periods)
    stock.periods = time_periods
    stock.name = re.findall("See the company profile for (.*?)\(%s\)" % ticker_symbol, profile.get_text())[0].strip()
    stock.name = format_company_name(stock.name)
    stock.continuous_dividend_growth = continuous_dividend_increases(stock)
    return stock


def calc_median_dividend_CAGR(stock):
    yields = calculate_dividend_increase(stock)


def calculate_dividend_increase(stock):
    history = stock.dividend_history
    yields = []
    annual_dividend = 0
    payout_per_year = 0
    year_regex = re.compile("^(\d+)")
    year = ""
    for entry in history:
        temp = re.search(year_regex, entry[0]).group(0)
        if temp == year:
            annual_dividend += entry[1]
            payout_per_year += 1
        else:
            if year != "":
                yields.append(annual_dividend/payout_per_year)
                year = temp
                payout_per_year = 1
                annual_dividend = entry[1]
            else:
                year = temp
                annual_dividend += entry[1]
                payout_per_year += 1
    return yields


def continuous_dividend_increases(stock):
    yields = calculate_dividend_increase(stock)
    for i, j in enumerate(yields[:-1]):
        if j > yields[i+1]:
            continue
        else:
            return False
    return True


def get_dividend_history(ticker, n):
    """
    @desc   - get historical dividend payout information
    @param  - ticker: the stock whose data will be gathered
    @param  - n: an integer representing the number of years to gather data for
    @return - returns: list of dividend returns
    """
    now = datetime.today() - timedelta(days=1)
    d1 = (now.year-n, now.month, now.day)
    d2 = (now.year, now.month, now.day)
    file_handler = fetch_historical_yahoo(ticker, d1, d2, dividends=True)
    yields = [(line.strip().split(",")[0], float(line.strip().split(",")[1])) for line in file_handler.readlines()[1:]]
    return yields


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
    returns = quotes_historical_yahoo_ohlc(ticker.upper(), d1, d2)
    return returns


def format_company_name(name):
    if "(The)" in name:
        name = re.sub("\s*\(The\).+", "", name)
        name = "The " + name
    if "Commo" in name:
        name = re.sub("\s*Commo.+", "", name)
    return name


def compound_annual_growth_rate(ticker, n=5):
    result = get_historical_price_data(ticker, n)
    then_close = result[0][4]
    today_close = result[-1][4]
    cagr = ((today_close / then_close) ** (1/n)) - 1
    return cagr


def print_summary(stock):
    print(stock.name)
    print("    {} consecutive years of dividend increases: {}".format(stock.periods, str(stock.continuous_dividend_growth)))
    print("    Dividend yield is at least 2% but less than 8%: {:.2f}%".format(stock.dividend_yield*100))
    # print("    Median of 1-year, 3-year, and 5-year compound annual growth rates is at least 6%")
    print("    Median of dividend 5-year CAGR is at lest 6%: {}%")
    print("%" * 80)


if __name__ == "__main__":
    ticker = sys.argv[1].upper().strip()
    periods = int(sys.argv[2])
    if ticker == "DIVGROW":
        tickers = sorted(["KO", "T", "CSCO", "BA", "MSFT", "AAPL", "NTT", "CVX", "INTC", "PG", "PNNT", "ABBV", "AFL",
                          "O", "TGT", "BBL", "CB", "CMI", "D", "DIS", "ES", "EXG", "F", "GD", "GILD", "GPS", "HP",
                          "IBM", "JNJ", "KMB", "LMT", "MAIN", "MCD", "MMM", "MO", "NEA", "NKE", "NOC", "OHI", "PFE",
                          "QCOM", "RAI", "RTN", "STAG", "TROW", "TRV", "UNP", "UPS", "VLO", "WBA", "WFC", "WMT", "XOM"])
        # large_caps = sorted(["CHL", "PG", "IBM", "KO", "SNY", "T", "TM", "TSM", "UL"])
        test = ["KO", "T"]
        results = []
        for ticker in tickers:
            try:
                result = get_statistics(ticker, periods)
                if result.continuous_dividend_growth is True and result.dividend_yield > 0.02: #  and result.compound_annual_growth_rate + result.dividend_yield > 0.12:
                    results.append(result)
            except:
                pass
        results.sort(key=operator.attrgetter("dividend_yield"))
        for result in reversed(results):
            print_summary(result)
    else:
        result = get_statistics(ticker, periods)
        print_summary(result)
