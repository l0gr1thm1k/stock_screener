import connexion

from screener.screen import Stock


def post_screen(ticker):  # noqa: E501
    """Take an input ticker string and get back current stock info

    Get back a list of stock properties. # noqa: E501

    :param ticker: 
    :type ticker: dict | bytes

    :rtype: ResponseObject
    """
    company_ticker = ticker['ticker'].upper()

    stock = Stock(company_ticker)
    curated_results = {"companyDescription": stock.description,
                       "companyName": stock.name,
                       "companyTicker": stock.ticker,
                       "debtToEquityRatio": stock.debt_to_equity,
                       "dividendCAGR": stock.dividend_compound_annual_growth_rate,
                       "dividendIncrease": stock.continuous_dividend_increases,
                       "dividendPayoutRatio": stock.dividend_payout_ratio,
                       "dividendYield": stock.dividend_yield,
                       "priceToEarningsRatio": stock.price_to_earnings_ratio,
                       "starRating": stock.star_rating,
                       "stockDiscount": stock.discount,
                       "stockFairValue": stock.graham_number,
                       "stockPrice": stock.price}
    return curated_results
