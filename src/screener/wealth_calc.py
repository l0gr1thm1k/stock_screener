
def calc(principle, salary, savings_rate, inflation_rate=0.07, dividend_yield=0.03, periods=32):
    principle_invested = 0
    # print("{:<15}\t{:<15}\t{:<15}\t{:<15}".format("NetWorth", "Principle", "Monthly Savings", "Annual Dividends"))
    for i in range(periods):
        yearly_savings = (salary * savings_rate)
        monthly_savings = yearly_savings / 12
        principle_invested += yearly_savings
        principle += yearly_savings
        principle = principle + principle * inflation_rate
        dividends = principle * dividend_yield
        principle = principle + dividends
        # print(round(principle, 2))
        print("${:<15,.2f}\t${:<15,.2f}\t${:<15,.2f}\t${:<15,.2f}".format(principle,
                                                            principle_invested,
                                                            monthly_savings,
                                                            dividends))


if __name__ == '__main__':
    calc(3767, 0, 0.5, periods=10, dividend_yield=0.054, inflation_rate=0.07)