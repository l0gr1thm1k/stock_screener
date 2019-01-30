# Connect to a web page and scrape it's contents.


from bs4 import BeautifulSoup
from urllib.request import urlopen


def make_soup(url):
    """
    @desc   - make a BeautifulSoup tree object for parsing
    @param  - url: the url destination to turn into soup
    @return - soup: the soup tree object
    """
    request = urlopen(url)
    raw_text = request.read()
    soup = BeautifulSoup(raw_text, "html.parser")
    return soup


if __name__ == '__main__':
    BASE_URL = "https://finance.google.com/finance?q={}"
    ticker_symbol = "jnj"
    url = BASE_URL.format(ticker_symbol.upper())

    soup = make_soup(url)
    print(soup)