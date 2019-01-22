#!/usr/bin/python3

import datetime
import re
import requests
import sys

from alpha_vantage.alpha_vantage import AlphaVantage
from good_morning.good_morning import KeyRatiosDownloader, FinancialsDownloader
from nasdaq.nasdaq_scrape import parse_finance_page
from numpy import sqrt
from utils import utils


kr = KeyRatiosDownloader()
kf = FinancialsDownloader()
av = AlphaVantage()


class Stock:
    """
    a basic class to hold stock properties as objects.
    """
    def __init__(self, ticker_symbol, periods=5):
        self.periods = periods
        self.ticker = ticker_symbol
        self.frames, self.name = kr.download(self.ticker)
        self.financials = kf.download(self.ticker)
        self.returns = av.send_request("TIME_SERIES_DAILY", self.ticker)
        self.today = utils.get_today_str()
        self.nasdaq_statistics = parse_finance_page(self.ticker)

        self.continuous_dividend_increases = self._continuous_dividend_increases()
        self.price = self._get_price()
        self.dividend_yield = self._get_dividend_yield()
        self.price_to_earnings_ratio = self._get_price_to_earnings_ratio()
        self.dividend_compound_annual_growth_rate = self._get_dividend_compound_annual_growth_rate(self.periods)
        self.dividend_payout_ratio = self._get_dividends_to_eps_ratio()
        self.debt_to_equity = self._get_debt_to_equity_ratio()
        self.graham_number = self._get_graham_number()
        self.discount = self._get_discount_rate()
        self.star_rating = self._get_star_rating()

    def _continuous_dividend_increases(self):
        """

        :return:
        """
        yields = self.frames[0].iloc[6][-self.periods:]
        present_yield = 0.0
        for i in yields:
            if i > present_yield:
                present_yield = i
            else:
                return False
        return True

    def _get_price(self):
        """
        This should be refactored to use the M* data

        :return:
        """
        try:
            price = float(self.returns['Time Series (Daily)'][self.today]['4. close'])
        except KeyError:
            last_business_day = utils.get_most_recent_date(list(self.returns['Time Series (Daily)'].keys()))
            price = float(self.returns['Time Series (Daily)'][last_business_day]['4. close'])

        return round(price, 2)

    def _get_dividend_yield(self):
        """
        Should be refactored to use M* data.

        :return:
        """
        div_yield = self.nasdaq_statistics['key_stock_data']['Current Yield']
        div_yield = float(re.findall('\d+\.\d*', div_yield)[0])
        return div_yield

    def _get_price_to_earnings_ratio(self):
        """

        :return:
        """
        pe_ratio = float(self.nasdaq_statistics['key_stock_data']['P/E Ratio'])
        return pe_ratio

    def _get_dividend_compound_annual_growth_rate(self, periods):
        """

        :param periods:
        :return:
        """
        indices = [str(element.year) for element in self.frames[0].columns[-periods:]]
        annualized_dividend_payments = [self.frames[0][index]['Dividends USD'] for index in indices]

        start_value = annualized_dividend_payments[0]
        end_value = annualized_dividend_payments[-1]
        growth_rate = ((end_value / start_value) ** (1 / periods) - 1) * 100
        return round(growth_rate, 2)

    def _get_dividends_to_eps_ratio(self):
        """

        :return:
        """
        index = str(self.frames[0].columns[-1].year)

        # dividend_payment = data[index]['Dividends USD']
        # earnings_per_share = data[index]['Earnings Per Share USD']
        # payout_ratio = round((dividend_payment / earnings_per_share) * 100, 2)
        payout_ratio = self.frames[0][index]['Payout Ratio % *']
        return payout_ratio

    def _get_graham_number(self):
        """
        Traditionally the constant in the equation is calculated as follows:
            EPS = 15
            BPS = 1.5
            CONSTANT = EPS * BPS = 22.5

        However, the upper bound of EPS for defensive investing I am willing to risk is sixteen, so this modifies our
        constant to be:

            CONSTANT = 16 * 1.5 = 24

        :return graham_number:
        """

        index = self.frames[0].columns[-1]
        book_value_per_share = self.frames[0][index]['Book Value Per Share * USD']
        earnings_per_share = self.frames[0][index]['Earnings Per Share USD']
        graham_number = round(sqrt(24 * earnings_per_share * book_value_per_share), 2)

        return graham_number

    def _get_discount_rate(self):
        """

        :return float: a percentage of discount rate. positive means there exists a discount, negative mean the
        equity is overpriced.
        """
        return round(((self.graham_number / self.price) - 1) * 100, 2)

    def _get_debt_to_equity_ratio(self):
        """

        :return:
        """
        index = str(self.frames[8].columns[-1].year)
        equity = self.frames[8][index]["Total Stockholders' Equity"]
        liabilities = self.frames[8][index]['Total Liabilities']
        debt_to_equity_ratio = round((liabilities / equity) * 100, 2)
        return debt_to_equity_ratio

    def _get_star_rating(self):
        """

        :return:
        """
        star = "\N{BLACK STAR}"
        rating = ""
        if self.continuous_dividend_increases is True:
            rating = rating + star
        if 2.0 <= self.dividend_yield <= 8.0:
            rating = rating + star
        if self.dividend_compound_annual_growth_rate >= 6.0:
            rating = rating + star
        if self.price_to_earnings_ratio <= 16.0:
            rating = rating + star
        if self.dividend_payout_ratio <= 60.0:
            rating = rating + star
        if self.debt_to_equity <= 60.0:
            rating = rating + star
        if self.discount >= 10.0:
            rating = rating + star
        return rating

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
    comp_annual_growth_rate = ((today_close / then_close) ** (1/n)) - 1
    return comp_annual_growth_rate




def print_summary(stock):
    print(stock.name.strip() + " (" + stock.ticker + ")")
    print("    {} consecutive years of dividend increases: {}".format(stock.periods,
                                                                      str(stock.continuous_dividend_increases)))
    print("    Stock's fair value: ${:.2f}".format(stock.graham_number))
    print("    Stock's price: ${:.2f}".format(stock.price))
    print("    Dividend yield is at least 2% but less than 8%: {:.2f}%".format(stock.dividend_yield))
    print("    Median of dividend {}-year compound annual growth is at least 6%: {:.2f}%".format(stock.periods,
                                                                                                 stock.dividend_compound_annual_growth_rate))
    print("    Price to Earnings ratio is less than 16: {:.2f}".format(stock.price_to_earnings_ratio))
    print("    Ratio of dividends to earnings per share is less than 60%: {:.2f}%".format(stock.dividend_payout_ratio))
    print("    Debt to equity ratio is less than 60%: {:.2f}%".format(stock.debt_to_equity))
    print("    Price discount is at least 10% of fair value estimate: {:.2f}%".format(stock.discount))
    print("    Star Rating: {}".format(stock.star_rating))
    print("%" * 80)



if __name__ == "__main__":
    ticker = sys.argv[1].upper().strip()
    this_stock = Stock(ticker)
    print_summary(this_stock)
    '''
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
'''