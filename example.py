#!/usr/bin/python3

from matplotlib.finance import *
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.request import urlopen
import urllib
import re
import requests
import sys
import math


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
    try:
        request = urlopen(url)
    except:
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
    ticker = url.split("/")[-1]
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
    try:
        profile = make_soup(stock.urls["profile"])
        statistics = make_soup(stock.urls["key-statistics"])
    except KeyError:
        return stock
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

    stock.current_price = financial_data["currentPrice"]["raw"]
    try:
        book_value = default_key_statistics["bookValue"]["raw"]
        trailing_eps = default_key_statistics["trailingEps"]["raw"]
        graham = calc_graham_num(trailing_eps, book_value)
        stock.discount = (graham / stock.current_price) - 1
    except KeyError:
        stock.discount = "N/A"
    # stock.price_to_book = default_key_statistics["priceToBook"]["raw"] # missing 'raw' field
    # stock.beta = default_key_statistics["beta"]["raw"] # missing 'raw' field
    # stock.forward_eps = default_key_statistics["forwardEps"]["raw"]

    # stock.peg_ratio = default_key_statistics["pegRatio"]["raw"] # missing 'raw' field
    if "raw" in financial_data["debtToEquity"]:
        stock.debt_to_equity = financial_data["debtToEquity"]["raw"]
    elif financial_data["debtToEquity"] == {}:
        stock.debt_to_equity = "N/A"
    else:
        stock.debt_to_equity = financial_data["debtToEquity"]
        print(stock.debt_to_equity)
        sys.exit(1)
    # stock.free_cash_flow = financial_data["freeCashflow"]["raw"]
    # stock.operating_cash_flow = financial_data["operatingCashflow"]["raw"]
    try:
        stock.annual_dividend = float(re.findall('"dividendRate":{"raw":(.*?),', soup.get_text())[0])
        stock.dividend_yield = float(stock.annual_dividend / stock.current_price)
        stock.dividend_payout_ratio = float(re.findall('payoutRatio".*?(\d*\.?\d+)',  statistics.get_text())[0])
    except IndexError:
        stock.annual_dividend = 0.0
        stock.dividend_yield = 0.0
        stock.dividend_payout_ratio = 0.0
    stock.price_to_earnings = float(re.findall("PE Ratio.*?TTM.*?(\d+\.\d+)", soup.get_text())[0])
    stock.compound_annual_growth_rate = compound_annual_growth_rate(stock.ticker, time_periods)
    stock.dividend_history = get_dividend_history(stock.ticker, time_periods)
    stock.periods = time_periods
    stock.name = re.findall("See the company profile for (.*?)\(%s\)" % ticker_symbol, profile.get_text())[0].strip()
    stock.name = format_company_name(stock.name)
    stock.continuous_dividend_growth = continuous_dividend_increases(stock)
    stock.dividend_cagr_rates = calc_median_dividend_cagr(stock)
    stock.rating = ""
    if stock.continuous_dividend_growth is True:
        stock.rating += "*"
    if 0.08 > stock.dividend_yield > 0.02:
        stock.rating += "*"
    if stock.dividend_cagr_rates >= 0.06:
        stock.rating += "*"
    if stock.price_to_earnings <= 16:
        stock.rating += "*"
    if stock.dividend_payout_ratio <= 0.6:
        stock.rating += "*"
    if stock.debt_to_equity == "N/A":
        pass
    elif stock.debt_to_equity <= 60.0:
        stock.rating += "*"
    if stock.discount == "N/A":
        pass
    elif stock.discount >= 0.1:
        stock.rating += "*"
    return stock


def calc_graham_num(eps, book):
    try:
        return math.sqrt(22.5*eps*book)
    except ValueError:
        return float('-inf')

def calc_median_dividend_cagr(stock):
    yields = calculate_dividend_increase(stock)
    current_yield = stock.annual_dividend / 4  # will have to fix this later
    compound_annual_growth_rates = []
    for index, old_yield in enumerate(yields):
        rate = ((current_yield / old_yield) ** (1/ (index+1) )) - 1
        compound_annual_growth_rates.append(rate)
    return median(compound_annual_growth_rates)


def median(x):
    try:
        if len(x) % 2 != 0:
            return sorted(x)[int(len(x)/2)]
        else:
            mid_1 = len(x) // 2
            mid_2 = mid_1 + 1
            mid_avg = (sorted(x)[mid_1] + sorted(x)[mid_2])/2
            return mid_avg
    except IndexError:
        return 0.0


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
    try:
        print(stock.name.strip() + " (" + stock.ticker + ")")
        print("    {} consecutive years of dividend increases: {}".format(stock.periods, str(stock.continuous_dividend_growth)))
        print("    Dividend yield is at least 2% but less than 8%: {:.2f}%".format(stock.dividend_yield*100))
        print("    Median of dividend {}-year compound annual growth is at least 6%: {:.2f}%".format(stock.periods, stock.dividend_cagr_rates*100))
        print("    Price to Earnings ratio is less than 16: {}".format(stock.price_to_earnings))
        print("    Ratio of dividends to earnings per share is less than 60%: {:.2f}%".format(stock.dividend_payout_ratio * 100))
        if type(stock.debt_to_equity) is float:
            print("    Debt to equity ratio is less than 60%: {:.2f}%".format(stock.debt_to_equity))
        else:
            print("    Debt to equity ratio is less than 60%: {}".format(stock.debt_to_equity))
        if type(stock.discount) is float:
            print("    Price discount is at least 10% of fair value estimate: {:.2f}%".format(stock.discount*100))
        else:
            print("    Price discount is at least 10% of fair value estimate: {}%".format(stock.discount))
        print("    Star Rating: {}".format(stock.rating))
        print("%" * 80)
    except AttributeError:
        pass


if __name__ == "__main__":
    ticker = sys.argv[1].upper().strip()
    periods = int(sys.argv[2])
    if ticker == "DIVGROW" or ticker == "WINNERS":
        # with open("watch_list.txt").readlines() as watch_list:
        if ticker == "DIVGROW":
            watch_list = open("watch_list.txt", "rb").readlines()
        else:
            watch_list = open("winners", "rb").readlines()
        summed_results = []
        for line in watch_list:
            tickers = [x.decode("utf-8") for x in line.strip().split()]
            results = []
            for ticker in tickers:
                try:
                    result = get_statistics(ticker, periods)
                    results.append(result)
                except:
                    print("Issue parsing {}".format(ticker))
                    pass
            # results.sort(key=lambda r: (r.rating, r.dividend_yield))
            summed_results += results
        summed_results.sort(key=lambda r: (r.rating, r.dividend_yield))
        for result in reversed(summed_results):
            print_summary(result)
    else:
        try:
            result = get_statistics(ticker, periods)
            print_summary(result)
        except:
            print("Issue parsing {}".format(ticker), file=sys.stderr)
            sys.exit(0)
