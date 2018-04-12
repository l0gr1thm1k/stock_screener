import numpy as np
import re


def graham_number(eps, book):
    """
    This is a number to measure a stock's 'fair value'. It is calculated simply as:

        sqrt( 22.5 * Earnings Per Share * Book Value Per Share)

    The resulting number can be thought of as the maximum price an investor should pay for a stock with that EPS and
    Book value. More can be learned about this metric on Wikipedia and investing websites:

        https://en.wikipedia.org/wiki/Graham_number

    :param eps: a float number that is the earnings per share a stock makes.
    :param book: The a float number which is the book value per share for a stock.
    :return graham_num: The theoretical maximum price that should be paid for a stock.
    """
    assert type(eps) is float and eps > 0
    assert type(book) is float and book > 0
    float_graham_num = np.sqrt(22.5 * eps * book)
    graham_num = np.around([float_graham_num], decimals=2)[0]
    return graham_num


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


if __name__ == '__main__':
    earnings_per_share = 5.76
    book_per_share = 5.29

    x = [4, 5, 6]
    print(median(x))
    print(np.median(x))