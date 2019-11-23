from datetime import datetime


def parse_mdy(str_: str):
    return datetime.strptime(str_, '%m/%d/%Y')


def date_to_dmy(date_: datetime):
    return datetime.strftime(date_, '%d/%m/%Y')


def dates_are_on_same_day(date_1: datetime, date_2: datetime):
    return date_1.day == date_2.day and date_1.month == date_2.month and date_1.year == date_2.year
