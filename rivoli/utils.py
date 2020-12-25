import json
from datetime import datetime, date
from typing import Any, Dict, List, Union


def parse_mdy(str_: str) -> date:
    return datetime.strptime(str_, '%m/%d/%Y').date()


def date_to_dmy(date_: date) -> str:
    return date_.strftime('%d/%m/%Y')


def parse_ymd(str_: str) -> date:
    return datetime.strptime(str_, '%Y/%m/%d').date()


def date_to_ymd(date_: date) -> str:
    return date_.strftime('%Y/%m/%d')


def write_json(dict_: Union[List, Dict[str, Any]], filename: str) -> None:
    with open(filename, 'w') as file_:
        json.dump(dict_, file_)


def write_str(str_: str, filename: str) -> None:
    with open(filename, 'w') as file_:
        file_.write(str_)


def dates_are_on_same_day(date_1: datetime, date_2: datetime) -> bool:
    return date_1.day == date_2.day and date_1.month == date_2.month and date_1.year == date_2.year


def month_to_word(month: int) -> str:
    map_ = {
        1: 'Janvier',
        2: 'Février',
        3: 'Mars',
        4: 'Avril',
        5: 'Mai',
        6: 'Juin',
        7: 'Juillet',
        8: 'Août',
        9: 'Septembre',
        10: 'Octobre',
        11: 'Novembre',
        12: 'Décembre',
    }
    return map_[month]


def datetime_to_french_month(date_: datetime) -> str:
    year = datetime.strftime(date_, '%Y')
    month = month_to_word(date_.month)
    return '{} {}'.format(month, year)
