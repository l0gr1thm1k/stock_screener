from tabulate import tabulate

def crossover_point(desired_monthly_income, monthly_deposit, formatting):
    dividend_yield = 0.04
    dividend_growth = 1.06
    stock_growth = 1.06
    table = []
    headers = ["Month", "Shares", "Share Price", "Dividend", "Mthly Income"]
    month = 1
    shares = monthly_deposit
    share_price = 1.000
    dividend = round((share_price / 12) * dividend_yield, 5)
    monthly_income = round(shares * dividend, 2)

    
    #print("\t".join(headers))
    #print("\t".join([str(x) for x in [month, shares, share_price, dividend, monthly_income]]))
    # table.append(headers)
    table.append([str(x) for x in [month, shares, share_price, dividend, monthly_income]])
    while monthly_income < desired_monthly_income:
        month += 1

        shares = round(shares + monthly_deposit + dividend, 2)
        monthly_income = round(shares * dividend, 5)
        
        # print("\t".join([str(x) for x in [month, shares, share_price, dividend, monthly_income]]))
        table.append([str(x) for x in [month, shares, share_price, dividend, monthly_income]])
        
        if month % 12 == 0:
            share_price *= stock_growth
            share_price = round(share_price, 5)

            dividend *= dividend_growth
            dividend = round(dividend, 5)

            # monthly_deposit *= 1.1
    print(tabulate(table, headers=headers, tablefmt=formatting))
    print("\nYou will reach a monthly income of ${:.2f} in {} years".format(monthly_income, round(month / 12, 1)))

    
if __name__ == '__main__':
    import sys
    crossover_point(60000, 7000, 'psql')
