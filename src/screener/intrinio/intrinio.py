import intrinio_sdk

from dateutil.relativedelta import relativedelta
from datetime import datetime
from numpy import nan, sqrt

API_KEY = 'OjliMWY5NzAwNDFiNjM5MzU2OWJiODlmODg0MTAyMDM2'
# API_KEY = 'OjQxMjczNjRjYWRiMTIyZmFkZDYyNGFmNTY1Nzg1NmJl'

class Stock:

    intrinio_sdk.ApiClient().configuration.api_key['api_key'] = API_KEY
    security_api = intrinio_sdk.SecurityApi()
    company_api = intrinio_sdk.CompanyApi()


    def __init__(self, ticker, industry=None, periods=5):

        self.ticker = ticker.upper()
        self.industry = industry
        self.periods = periods

        ###################
        # GET DATE RANGES #
        ###################
        
        self.end_date = datetime.today()
        self.start_date = self.end_date - relativedelta(years=self.periods)
        
        #####################################
        # GET OR CALCULATE STOCK PROPERTIES #
        #####################################
    
        self.dividend_yield = self._get_company_numeric_attribute('dividendyield')
        self.dividend_payout_ratio = self._get_company_numeric_attribute('divpayoutratio')
        self.price_to_earnings_ratio = self._get_company_numeric_attribute('pricetoearnings')
        self.debt_to_equity = self._get_company_numeric_attribute('debttoequity')
        self.annualized_dividends = self._get_annualized_dividends()
        self.name = self._get_name()
        self.price = self._get_price()
        self.continuous_dividend_increases = self._continuous_dividend_increases()
        self.dividend_compound_annual_growth_rate = self._get_dividend_compound_annual_growth_rate(self.periods)
        self.graham_number = self._get_graham_number()
        self.discount = self._get_discount_rate()
        self.star_rating = self._get_star_rating()
        
    def _get_name(self):
        return self.company_api.get_company_data_point_text(self.ticker, 'name')

    def _get_price(self):
        return self.security_api.get_security_realtime_price(self.ticker).last_price

    def _get_company_numeric_attribute(self, tag):
        return self.company_api.get_company_data_point_number(self.ticker, tag)

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
        basic_earnings_per_share = self._get_company_numeric_attribute('basiceps')
        book_value_per_share = self._get_company_numeric_attribute('bookvaluepershare')
        return round(sqrt(24 * basic_earnings_per_share * book_value_per_share), 2)
 
    def _continuous_dividend_increases(self):
        past_dividend = 0.0
        for dividend_payment in self.annualized_dividends:
            if dividend_payment < past_dividend:
                return False
            past_dividend = dividend_payment
            
        return True

    def _get_annualized_dividends(self):
        historical_dividend_data = self.company_api.get_company_historical_data(self.ticker, 'dividend', start_date=self.start_date,
                                                                                end_date=self.end_date, sort_order='asc').historical_data
        current_year = historical_dividend_data[0].date.year
        dividends = []
        dividend_payed = 0
        for element in historical_dividend_data:
            if element.date.year == current_year:
                dividend_payed += element.value
            else:
                dividends.append(round(dividend_payed, 2))
                div_payed = element.value
                current_year = element.date.year
            if len(dividends) >= self.periods:
                break
            
        return dividends
        
    def _get_dividend_compound_annual_growth_rate(self, periods):

        if sum(self.annualized_dividends) > 0:
            pass
        else:
            return 0.0
        start_value = self.annualized_dividends[0]
        end_value = self.annualized_dividends[-1]
        growth_rate = ((end_value / start_value) ** (1 / periods) - 1)
        
        return round(growth_rate, 4)

    def _get_discount_rate(self):
        """

        :return float: a percentage of discount rate. positive means there exists a discount, negative mean the
        equity is overpriced.
        """
        if self.graham_number > self.price:
            # if underpriced
            difference = self.graham_number - self.price
            discount = round((difference / self.graham_number), 4)
            return discount
        else:
            # if overpriced
            difference = self.price - self.graham_number
            discount = -round((difference / self.price), 4)
        return discount

    def _get_star_rating(self):
        """

        :return:
        """
        star = "\N{BLACK STAR}"
        empty_star = "\N{WHITE STAR}"
        rating = ""
        conditions = [self.continuous_dividend_increases is True,
                      0.02 <= self.dividend_yield <= 0.08,
                      self.dividend_compound_annual_growth_rate >= 0.06,
                      self.price_to_earnings_ratio <= 16.0,
                      0.0 < self.dividend_payout_ratio <= 0.6,
                      self.debt_to_equity <= 0.6,
                      self.discount >= 0.1]
        for condition in conditions:
            if condition is not nan and condition:
                rating = rating + star
        num_empty_stars = 7 - len(rating)
        empty_stars = empty_star * num_empty_stars
        rating = rating + empty_stars
        return rating


def format_company_name(name):
    if "(The)" in name:
        name = re.sub("\s*\(The\).+", "", name)
        name = "The " + name
    if "Commo" in name:
        name = re.sub("\s*Commo.+", "", name)
    return name


def print_msg(text: str, newline: bool = False) -> None:
    """
    Print a banner

    :param text: text to print
    :param newline: whether or not to print a newline before banner
    """

    if newline:
        print()
    print("% {: <117}%".format(text))
    

def print_summary(stock):
 
    msgs = [" ",
            stock.name.strip() + " (" + stock.ticker + ")",
            " ",
            "    {} consecutive years of dividend increases: {}".format(stock.periods, str(stock.continuous_dividend_increases)),
            "    Dividend yield is at least 2% but less than 8%: {:.2f}%".format(stock.dividend_yield * 100),
            "    Median of dividend {}-year compound annual growth is at least 6%: {:.2f}%".format(stock.periods,
                                                                                                   stock.dividend_compound_annual_growth_rate * 10),
            "    Ratio of dividends to earnings per share is less than 60%: {:.2f}%".format(stock.dividend_payout_ratio * 100),
            " ",
            "    Price to Earnings ratio is less than 16: {:.2f}".format(stock.price_to_earnings_ratio),
            "    Debt to equity ratio is less than 0.60: {:.2f}".format(stock.debt_to_equity),
            " ",
            "    Stock's fair value: ${:.2f}".format(stock.graham_number),
            "    Stock's price: ${:.2f}".format(stock.price),
            "    Price discount is at least 10% of fair value estimate: {:.2f}%".format(stock.discount * 100),
            " ",
            "    Star Rating: {}".format(stock.star_rating),
            " "]
    if stock.industry is not None:
        msgs.insert(3, "    Sector: {}".format(stock.industry))
        msgs.insert(4, " ")
        
    print("%" * 120)
    for msg in msgs:
        print_msg(msg)
    
    print("%" * 120)


if __name__ == '__main__':
    import sys
    ticker = sys.argv[1]
    stock = Stock(ticker)
    print_summary(stock)
