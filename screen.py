#!/usr/bin/python3

import re
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
            # last_business_day = utils.get_most_recent_date(list(self.returns['Time Series (Daily)'].keys()))
            last_business_day = list(self.returns['Time Series (Daily)'].keys())[0]
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
        debt_to_equity_ratio = round(liabilities / equity, 2)
        return debt_to_equity_ratio

    def _get_star_rating(self):
        """

        :return:
        """
        star = "\N{BLACK STAR}"
        rating = ""
        conditions = [self.continuous_dividend_increases is True,
                      2.0 <= self.dividend_yield <= 8.0,
                      self.dividend_compound_annual_growth_rate >= 6.0,
                      self.price_to_earnings_ratio <= 16.0,
                      self.dividend_payout_ratio <= 60.0,
                      self.debt_to_equity <= 0.6,
                      self.discount >= 10.0]
        for condition in conditions:
            if condition:
                rating = rating + star
        return rating


def format_company_name(name):
    if "(The)" in name:
        name = re.sub("\s*\(The\).+", "", name)
        name = "The " + name
    if "Commo" in name:
        name = re.sub("\s*Commo.+", "", name)
    return name


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
    print("    Debt to equity ratio is less than 0.60: {:.2f}".format(stock.debt_to_equity))
    print("    Price discount is at least 10% of fair value estimate: {:.2f}%".format(stock.discount))
    print("    Star Rating: {}".format(stock.star_rating))
    print("%" * 80)


if __name__ == "__main__":
    ticker = sys.argv[1].upper().strip()
    this_stock = Stock(ticker)
    print_summary(this_stock)
