import json
import urllib.request


class AlphaVantage:

    def __init__(self):
        """
        Initialize the AlphaVantage class to be associated to a user and API key.
        """
        self.user, self.key = self.import_user_credentials()

    @staticmethod
    def import_user_credentials():
        """
        Import a user's login name and API key to be used when making calls to the AlphaVantage API. The file name is
        hardcoded to "credentials.txt" and we assume that there is a username and key field seperated by a "=" sign.

        :return user: Return the username whose API key we will use when calling AlphaVantage.
        :return key: Return the API key to access financial information from AlphaVantage.
        """
        info = open("credentials.txt", "r").readlines()
        user = info[0].split("=")[1].strip()
        key = info[1].split("=")[1].strip()
        return user, key

    def send_request(self, func, ticker, interval=None, output='compact'):
        """
        Get the daily returns associated with a ticker argument.

        :param func: Function name to execute. One of:
            TIME_SERIES_INTRADAY
            TIME_SERIES_DAILY
            TIME_SERIES_DAILY_ADJUSTED
            TIME_SERIES_WEEKLY
            TIME_SERIES_WEEKLY_ADJUSTED
            TIME_SERIES_MONTHLY
            TIME_SERIES_MONTHLY_ADJUSTED
            
        :param ticker: A string argument representing a company's ticker (e.g. NVDA, IBM, CVX)
        :param interval: The rate at which to fetch prices. Defaults to None. Can be on of values
            1min
            5min
            15min
            30min
            60min
        :param output: The output type that AlphaVantage should return. Defaults to compact, possible values include
            compact
            full
        :return json_response: Return a json object with the daily return data.
        """
        base_url = "https://www.alphavantage.co/query?function={}&symbol={}&outputsize={}{}&apikey={}"
        if interval is None:
            formatted_url = base_url.format(func, ticker, output, '', self.key)
        else:
            formatted_url = base_url.format(func, ticker, output, '&interval=' + interval, self.key)

        with urllib.request.urlopen(formatted_url) as response:
            json_response = json.loads(response.read())
        return json_response


if __name__ == '__main__':
    import pprint
    av = AlphaVantage()
    print("user: {}".format(av.user))
    print("API key: {}".format(av.key))
    result = av.send_request("TIME_SERIES_DAILY", "NVDA")
    pp = pprint.PrettyPrinter(depth=4)
    pp.pprint(result)
