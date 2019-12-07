import logging
import requests
import traceback
import numpy as np
import json

from datetime import datetime, timedelta
from calendar import monthrange
from collections import Counter
from typing import List, Tuple, Dict

from rivoli.exceptions import FailedRequestingEcoCounterError
from rivoli.config import ECO_COUNTER_URL, ZAPIER_WEBHOOK_URL, SLACK_TEST_URL
from rivoli.utils import parse_mdy, dates_are_on_same_day, date_to_dmy, datetime_to_french_month


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

    @classmethod
    def month_rank(cls, day: datetime, month_count: int, month_rank: int, month: datetime):
        french_month = datetime_to_french_month(month)
        french_rank = 'meilleur' if month_rank == 0 else '{}ème meilleur'.format(month_rank + 1)
        headline = '{}: {} mois de l\'histoire avec {} passages.'.format(french_month, french_rank, month_count)
        return cls(headline=headline, details='', day=day)

    @classmethod
    def best_month_to_be(
        cls, day: datetime, count_so_far: int, previous_record_month: datetime, previous_record_count: int
    ):
        headline = (
            'Meilleur mois à ce stade d\'avancement avec {} passages. '
            'Précedent record: {} avec {} passages.'.format(
                count_so_far, datetime_to_french_month(previous_record_month), previous_record_count,
            )
        )
        return cls(headline=headline, details='', day=day)

    @classmethod
    def total_count(cls, day: datetime, total_count: int):
        headline = '{} passages depuis le début.'.format(total_count)
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


def day_is_last_day_of_month(day: datetime) -> bool:
    day_after = day + timedelta(days=1)
    return day_after.day == 1


def day_is_first_day_of_year(day: datetime) -> bool:
    return day.month == 1 and day.day == 1


def day_is_first_day_of_month(day: datetime) -> bool:
    return day.day == 1


def extract_total_count(count_history: CountHistory) -> int:
    return sum([day_count.count for day_count in count_history.daily_counts])


def extract_month_to_cumsum(count_history: CountHistory) -> Dict[Tuple[int, int], List[int]]:
    month_to_day_counts: Dict[Tuple[int, int], List[DayCount]] = {}
    for day_count in count_history.daily_counts:
        month = extract_month(day_count.date)
        month_to_day_counts[month] = month_to_day_counts.get(month, []) + [day_count]
    month_to_sorted_counts = {
        month: sorted(day_counts, key=lambda day_count: day_count.date)
        for month, day_counts in month_to_day_counts.items()
    }
    month_to_cumsum = {
        month: np.cumsum([x.count for x in sorted_counts]) for month, sorted_counts in month_to_sorted_counts.items()
    }
    return month_to_cumsum


def extract_month(day: datetime) -> Tuple[int, int]:
    return (day.year, day.month)


def is_best_month_to_be(day: datetime, count_history: CountHistory) -> Tuple[bool, int, Tuple[int, int], int]:
    month_to_cumsum = extract_month_to_cumsum(count_history)
    current_month = extract_month(day)
    month_range = monthrange(day.year, day.month)[1]
    month_advancement = day.day / month_range
    month_count_so_far = month_to_cumsum[current_month][-1]
    advancement_to_month = {}
    for other_month, cumcount in month_to_cumsum.items():
        if other_month == current_month:
            continue
        pct = np.percentile(cumcount, q=100 * month_advancement)
        advancement_to_month[pct] = other_month
    if not advancement_to_month:
        raise ValueError('Edge case not handled')
    best_other_advancement = max(advancement_to_month.keys())
    best_other_month = advancement_to_month[best_other_advancement]
    if month_count_so_far >= best_other_advancement:
        return True, month_count_so_far, best_other_month, int(best_other_advancement)
    return False, month_count_so_far, best_other_month, int(best_other_advancement)


def extract_rank_in_decreasing_list(value, sequence: list) -> int:
    if value not in sequence:
        raise ValueError('Value {} not in given sequence {}'.format(value, sequence))
    return np.where(np.sort(sequence)[::-1] == value)[0][0]


def extract_month_stats(day: datetime, count_history: CountHistory) -> Tuple[int, int, datetime]:
    month = extract_month(day)
    month_to_cumsum = extract_month_to_cumsum(count_history)
    month_to_total = {mnth: cumcount[-1] for mnth, cumcount in month_to_cumsum.items()}
    if month not in month_to_total:
        raise ValueError('Previous month not in history.')
    month_total = month_to_total[month]
    month_rank = extract_rank_in_decreasing_list(month_total, list(month_to_total.values()))
    return month_total, month_rank, day


def extract_relevant_facts(day: datetime, count_history: CountHistory) -> list:
    if not day_in_history(day, count_history):
        raise ValueError('Day {} is not in count history'.format(date_to_dmy(day)))
    relevant_facts: List[RelevantFact] = []
    if day_is_absolute_maximum(day, count_history):
        relevant_facts.append(RelevantFact.new_record(day))
    else:
        it_is, rank = day_is_absolute_top_k(day, count_history, k=10)
        if it_is:
            relevant_facts.append(RelevantFact.top_k(day, rank))
        else:
            if day_is_last_day_of_month(day):
                month_count, month_rank, previous_month_datetime = extract_month_stats(day, count_history)
                relevant_facts.append(RelevantFact.month_rank(day, month_count, month_rank, previous_month_datetime))
            elif not day_is_first_day_of_year(day) and day_is_yearly_maximum(day, count_history):
                relevant_facts.append(RelevantFact.new_yearly_record(day))
            elif not day_is_first_day_of_month(day) and day_is_monthly_record(day, count_history):
                relevant_facts.append(RelevantFact.new_monthly_record(day))
            else:
                it_is, count_so_far, (other_month_year, other_month_month), other_count = is_best_month_to_be(
                    day, count_history
                )
                if it_is:
                    previous_record_month = datetime(year=other_month_year, month=other_month_month, day=1)
                    relevant_facts.append(
                        RelevantFact.best_month_to_be(day, count_so_far, previous_record_month, other_count)
                    )
                else:
                    total_count = extract_total_count(count_history)
                    relevant_facts.append(RelevantFact.total_count(day, total_count))
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


def prepare_tweet(day: datetime, count_history: CountHistory) -> str:
    return prepare_message_for_std_out(day, count_history) + '\n#CompteurRivoli'


def pad_answer(answer):
    return [['09/01/2019', '0']] + answer


def get_tweet():
    answer = pad_answer(fetch_data(ECO_COUNTER_URL))
    today = datetime.now()
    count_history = CountHistory.from_url_answer(answer)
    yesterday = today - timedelta(days=1)
    return {'tweet': prepare_tweet(yesterday, count_history)}


def post_tweet():
    payload = get_tweet()
    logging.info(payload)
    requests.post(ZAPIER_WEBHOOK_URL, json.dumps(payload))


def post_text_to_slack(text: str) -> None:
    requests.post(url=SLACK_TEST_URL, data=json.dumps({'text': text}))


def lambda_handler(event, context):
    if event.get('test'):
        tweet = get_tweet()
        logging.info(tweet)
        post_text_to_slack(tweet['tweet'])
        return tweet
    post_tweet()


if __name__ == '__main__':
    answer = pad_answer(fetch_data(ECO_COUNTER_URL))
    today = datetime.now()
    for i in range(len(answer)):
        count_history = CountHistory.from_url_answer(answer[: (-i or len(answer))])
        day_of_publication = today - timedelta(days=i)
        day_to_test = today - timedelta(days=i + 1)
        try:
            print(date_to_dmy(day_of_publication))
            print(prepare_message_for_std_out(day_to_test, count_history))
        except Exception:
            print(date_to_dmy(day_of_publication))
            print(traceback.format_exc())
        print()
        print()
