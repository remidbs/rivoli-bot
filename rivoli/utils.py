from datetime import datetime


def parse_mdy(str_: str):
    return datetime.strptime(str_, '%m/%d/%Y')
