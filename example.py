#!/usr/bin/env python

from bs4 import BeautifulSoup
import pandas as pd
import sys

# url = "http://finance.yahoo.com/quote/%s"
# text = urllib.request.urlopen(url % "T")
# raw_text = text.read()
# soup = bs(raw_text, 'html.parser')

filename = sys.argv[1]
data = open(filename, "r")
soup = BeautifulSoup(data, "html.parser")

# calls, puts = soup.find_all(attrs={"class": "follow-quote-area"})


"""
def extract_data(x):
    arr = []
    for row in x.find_all("tr"):
        arr.append([])
        for data in row.find_all("td"):
            value = data.get_text().strip()
            arr[-1].append(value)
    arr = filter(lambda x: len(x) == 10, arr)
    return arr

calls = extract_data(calls)
puts = extract_data(puts)

columns = ["Strike",
           "ContractName",
           "Last",
           "Bid",
           "Ask",
           "Change",
           "PctChange",
           "Volume",
           "OpenInterest",
           "ImpliedVolatility"]

calls = pd.DataFrame(calls, columns=columns)
puts = pd.DataFrame(puts, columns=columns)

print(calls)
"""
