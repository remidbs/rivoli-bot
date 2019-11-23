import logging
import requests
import traceback

from datetime import datetime, timedelta
from collections import Counter
from typing import List, Tuple

from rivoli.exceptions import FailedRequestingEcoCounterError
from rivoli.config import ECO_COUNTER_URL
from rivoli.utils import parse_mdy, dates_are_on_same_day, date_to_dmy


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
        count = int(float(pair[1]))
        return cls(date=date, count=count)


class CountHistory:
    def __init__(self, daily_counts):
        self.daily_counts: List[DayCount] = daily_counts

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


def day_is_today(day):
    today = datetime.now()
    return dates_are_on_same_day(day, today)


def day_is_yesterday(day):
    yesterday = datetime.now() - timedelta(hours=24)
    return dates_are_on_same_day(day, yesterday)


class RelevantFact:
    def __init__(
        self, day, headline, details,
    ):
        self.day: datetime = day
        self.headline: str = headline
        self.details: str = details

    @classmethod
    def new_record(cls, day: datetime):
        headline = 'Record historique!'
        return cls(headline=headline, details='', day=day)

    @classmethod
    def top_k(cls, day: datetime, k: int):
        if k == 1:
            ordinal = 'Meilleur'
        else:
            ordinal = '{}ème meilleur'.format(k)
        headline = '{} jour historique!'.format(ordinal)
        return cls(headline=headline, details='', day=day)

    @classmethod
    def new_monthly_record(cls, day: datetime):
        headline = 'Record du mois!'
        return cls(headline=headline, details='', day=day)

    @classmethod
    def new_yearly_record(cls, day: datetime):
        headline = 'Record de l\'année!'
        return cls(headline=headline, details='', day=day)


def fetch_data(url) -> list:
    try:
        answer = requests.post(url)
        return answer.json()
    except Exception:
        logging.error(traceback.format_exc())
        raise FailedRequestingEcoCounterError()


def day_in_history(day: datetime, count_history: CountHistory):
    days_in_history = {date_to_dmy(day_count.date) for day_count in count_history.daily_counts}
    lookedup_day = date_to_dmy(day)
    return lookedup_day in days_in_history


def extract_day_count(day: datetime, count_history: CountHistory) -> int:
    if not day_in_history(day, count_history):
        raise ValueError('Day {} is not in count history'.format(date_to_dmy(day)))
    str_day_to_count = {date_to_dmy(day_count.date): day_count.count for day_count in count_history.daily_counts}
    return str_day_to_count[date_to_dmy(day)]


def day_is_absolute_maximum(day: datetime, count_history: CountHistory):
    day_count = extract_day_count(day, count_history)
    max_count = max([day_count.count for day_count in count_history.daily_counts])
    return day_count == max_count


def day_is_yearly_maximum(day: datetime, count_history: CountHistory):
    day_count = extract_day_count(day, count_history)
    same_year_counts = [day_count.count for day_count in count_history.daily_counts if day_count.date.year == day.year]
    return day_count == max(same_year_counts)


def day_is_monthly_record(day: datetime, count_history: CountHistory):
    day_count = extract_day_count(day, count_history)
    same_month_counts = [
        day_count.count for day_count in count_history.daily_counts if day_count.date.month == day.month
    ]
    return day_count == max(same_month_counts)


def day_is_absolute_top_k(day: datetime, count_history: CountHistory, k: int) -> Tuple[bool, int]:
    day_count = extract_day_count(day, count_history)
    all_counts = [day_count.count for day_count in count_history.daily_counts]
    top_k = sorted(all_counts)[-k:][::-1]
    for rank_minus_1, value in enumerate(top_k):
        if value == day_count:
            return True, rank_minus_1 + 1
    return False, -1


def day_is_not_first_day_of_year(day: datetime) -> bool:
    return not (day.month == 1 and day.day == 1)


def day_is_not_first_day_of_month(day: datetime) -> bool:
    return not (day.day == 1)


def extract_relevant_facts(day: datetime, count_history: CountHistory) -> list:
    if not day_in_history(day, count_history):
        raise ValueError('Day {} is not in count history'.format(date_to_dmy(day)))
    relevant_facts: List[RelevantFact] = []
    if day_is_absolute_maximum(day, count_history):
        relevant_facts.append(RelevantFact.new_record(day))
    elif day_is_not_first_day_of_year(day) and day_is_yearly_maximum(day, count_history):
        relevant_facts.append(RelevantFact.new_yearly_record(day))
    elif day_is_not_first_day_of_month(day) and day_is_monthly_record(day, count_history):
        relevant_facts.append(RelevantFact.new_monthly_record(day))
    else:
        it_is, rank = day_is_absolute_top_k(day, count_history, k=10)
        if it_is:
            relevant_facts.append(RelevantFact.top_k(day, rank))
    return relevant_facts


def extract_day_incipit(day: datetime):
    if day_is_today(day):
        return 'Aujourd\'hui'
    if day_is_yesterday(day):
        return 'Hier'
    return 'Le {}'.format(date_to_dmy(day))


def prepare_message_for_std_out(day: datetime, count_history: CountHistory) -> str:
    relevant_facts = extract_relevant_facts(day, count_history)
    count = extract_day_count(day, count_history)

    day_incipit = extract_day_incipit(day)
    plural = 's' if count > 1 else ''
    regular_message = '{}, il y a eu {} cycliste{}.'.format(day_incipit, count, plural)
    relevant_facts_message = '\n'.join([fact.headline for fact in relevant_facts])

    return '\n'.join([regular_message, relevant_facts_message])


if __name__ == '__main__':
    count_history = CountHistory.from_url_answer(fetch_data(ECO_COUNTER_URL))
    today = datetime.now()
    days_to_test = [today - timedelta(days=k) for k in range(100)]
    for day_to_test in days_to_test:
        try:
            print(date_to_dmy(day_to_test), prepare_message_for_std_out(day_to_test, count_history))
        except Exception as e:
            print(e)
