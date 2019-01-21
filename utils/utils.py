import datetime

from dateutil import parser


def get_today_str():
    """
    Take the current date and format the results to string.

    :return today_str: return a string formatted as YYYY-MM-DD
    """
    today = datetime.datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    return today_str


def get_most_recent_date(list_of_dates):
    """

    :param list_of_dates:
    :return:
    """
    dates = [(date, parser.parse(date)) for date in list_of_dates]
    dates.sort(key=lambda x: x[1], reverse=False)
    most_recent_date = dates[0][0]
    return most_recent_date
