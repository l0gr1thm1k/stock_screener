import datetime


def get_date_str():
    """
    Take the current date and format the results to string.

    :return today_str: return a string formatted as YYYY-MM-DD
    """
    today = datetime.datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    return today_str
