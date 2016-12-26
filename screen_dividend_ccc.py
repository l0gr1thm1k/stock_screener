#!/usr/bin/python3

import example as screen


def make_ccc_list():
    ccc_list = []
    with open("dividend_ccc.txt") as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip().split()
            ticker = line[0]
            industry = " ".join(line[1:])
            stock = screen.Stock(ticker)
            stock.industry = industry
            ccc_list.append(stock)
    return ccc_list


def get_industries(stock_list):
    industries = set()
    for stock in stock_list:
        industries.add(stock.industry)
    return sorted(list(industries))


def main():
    stocks = make_ccc_list()
    industries = get_industries(stocks)
    for industry in industries:
        print("#" * 80)
        print("# " + industry)
        print("#" * 80)
        for stock in stocks:
            if stock.industry == industry:
                thing = screen.get_statistics(stock.ticker)
                if hasattr(thing, "rating") and len(thing.rating) >= 6:
                    screen.print_summary(thing)


if __name__ == "__main__":
    main()