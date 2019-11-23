import logging
import requests
import traceback

from datetime import datetime
from collections import Counter

from rivoli.exceptions import FailedRequestingEcoCounterError
from rivoli.config import ECO_COUNTER_URL
from rivoli.utils import parse_mdy


class DayCount:
    def __init__(self, date, count):
        self.date: datetime = date
        self.count: int = count

    @classmethod
    def from_json(cls, dict_):
        return cls(date=dict_['date'].timestamp(), count=dict_['count'])

    def to_json(self):
        return {
            'date': datetime.fromtimestamp(self.date),
            'count': self.count,
        }

    @classmethod
    def from_pair(cls, pair: tuple):
        if len(pair) != 2:
            raise ValueError('Need a pair as argument, received {}'.format(pair))
        date = parse_mdy(pair[0])
        count = int(pair[1])
        return cls(date=date, count=count)


class CountHistory:
    def __init__(self, daily_counts):
        self.daily_counts: DayCount = daily_counts

    def to_json(self):
        return {'daily_counts': [day_point.to_json() for day_point in self.daily_counts]}

    @classmethod
    def from_json(cls, dict_: dict):
        return cls(daily_counts=[DayCount.from_json(day_count) for day_count in dict_['daily_counts']])

    @classmethod
    def from_url_answer(cls, data: list):
        pairs = data[:-1]
        if {len(pair) for pair in pairs} != {2}:
            raise ValueError(
                'Expecting a list of pairs, lengths received: {}'.format(
                    Counter([len(pair) for pair in pairs]).most_common()
                )
            )
        return cls(daily_counts=[DayCount.from_pair(pair) for pair in pairs])


def fetch_data(url):
    try:
        answer = requests.post(url)
        return answer.json()
    except Exception:
        logging.error(traceback.format_exc())
        raise FailedRequestingEcoCounterError()


def extract_relevant_facts(day: datetime, count_history: CountHistory):
    NotImplemented


if __name__ == '__main__':
    logging.info('holà')
    fetch_data(ECO_COUNTER_URL)
