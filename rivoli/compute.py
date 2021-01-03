import random
from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil
from typing import Callable, Dict, Iterable, List, Optional, Union

from rivoli.models import CountHistory, Hashtag, Month, Tweet
from rivoli.utils import date_to_dmy, month_to_french_word


def day_is_today(day: date) -> bool:
    return day == date.today()


def day_is_yesterday(day: date) -> bool:
    yesterday = date.today() - timedelta(days=1)
    return day == yesterday


def _safe_get_count(day: date, count_history: CountHistory) -> int:
    if day not in count_history.day_to_count:
        raise ValueError(f'Day {day} not found in count_history.')
    return count_history.day_to_count[day]


def _day_is_absolute_maximum(day: date, count_history: CountHistory) -> bool:
    day_count = _safe_get_count(day, count_history)
    max_count = max(count_history.day_to_count.values())
    return day_count == max_count


def _day_is_year_maximum(day: date, count_history: CountHistory) -> bool:
    day_count = _safe_get_count(day, count_history)
    same_year_counts = [day_count.count for day_count in count_history.daily_counts if day_count.date.year == day.year]
    return day_count == max(same_year_counts)


def _day_is_monthly_record(day: date, count_history: CountHistory) -> bool:
    day_count = _safe_get_count(day, count_history)
    same_month_counts = [
        day_count.count for day_count in count_history.daily_counts if day_count.date.month == day.month
    ]
    return day_count == max(same_month_counts)


def _day_rank(day: date, count_history: CountHistory) -> int:
    day_count = _safe_get_count(day, count_history)
    all_counts = list(count_history.day_to_count.values())
    return _optimistic_rank(day_count, all_counts)


def _optimistic_rank(target: int, values: Iterable[int]) -> int:
    for rank, value in enumerate(sorted(values, reverse=True)):
        if value == target:
            return rank
    raise ValueError('target not found in values.')


def _day_is_last_day_of_month(day: date) -> bool:
    day_after = day + timedelta(days=1)
    return day_after.day == 1


def _day_is_last_day_of_year(day: date) -> bool:
    return day.day == 31 and day.month == 12


def _day_is_first_day_of_year(day: date) -> bool:
    return day.month == 1 and day.day == 1


def _day_is_first_day_of_month(day: date) -> bool:
    return day.day == 1


def _extract_total_count(count_history: CountHistory) -> int:
    return sum(count_history.day_to_count.values())


def _get_month(day: date) -> Month:
    return Month(day.month, day.year)


def _number_is_funny(number: int) -> bool:
    if len(set(str(number))) == 1 and len(str(number)) >= 3:
        return True
    if number % (10 ** (len(str(number)) - 1)) == 0:
        return True
    return False


def _group_by_month(count_history: CountHistory) -> Dict[Month, List[int]]:
    result: Dict[Month, List[int]] = {}
    for day in count_history.daily_counts:
        month = _get_month(day.date)
        if month not in result:
            result[month] = []
        result[month].append(day.count)
    return result


def _group_by_year(count_history: CountHistory) -> Dict[int, List[int]]:
    result: Dict[int, List[int]] = {}
    for day in count_history.daily_counts:
        if day.date.year not in result:
            result[day.date.year] = []
        result[day.date.year].append(day.count)
    return result


def _cumulate(values: List[int]) -> List[int]:
    cumulated_sums: List[int] = []
    current_sum = 0
    for value in values:
        current_sum += value
        cumulated_sums.append(current_sum)
    return cumulated_sums


def _month_to_cumulate_sums(count_history: CountHistory) -> Dict[Month, List[int]]:
    month_to_counts = _group_by_month(count_history)
    return {month: _cumulate(counts) for month, counts in month_to_counts.items()}


def _get_month_range(month: Month) -> int:
    return monthrange(month.year, month.month)[1]


@dataclass
class HistoricalRecordEvent:
    @staticmethod
    def default_score() -> float:
        return 1.0

    @staticmethod
    def default_message() -> str:
        return 'Record historique !'


@dataclass
class MonthRecordEvent:
    day: date

    def default_score(self) -> float:
        if self.day.day >= 15:
            return 0.8
        if self.day.day <= 5:
            return 0
        return 0.5

    @staticmethod
    def default_message() -> str:
        return 'Record du mois !'


def _round_to_twentieth(float_: float) -> int:
    if float_ < 0 or float_ > 1:
        raise ValueError('Expecting float between 0 and 1')
    return int(ceil(float_ * 20) * 5)


def _capitalize_first_letter(str_: str) -> str:
    if not str_:
        return str_
    return str_[0].upper() + str_[1:]


@dataclass
class DayHistoricalRankEvent:
    rank: int
    among_nb_days: int

    def __post_init__(self):
        if self.rank >= self.among_nb_days:
            raise ValueError(
                f'rank must be strictly smaller than total nb days (resp. {self.rank} and {self.among_nb_days})'
            )

    def default_score(self) -> float:
        if self.rank / self.among_nb_days <= 0.05:
            return 0.8
        if self.rank / self.among_nb_days <= 0.3:
            return 0.5
        return 0

    def default_message(self) -> str:
        if self.rank <= 10:
            return _capitalize_first_letter(f'{_build_french_ordinal(self.rank)}meilleur jour historique.')
        top = _round_to_twentieth((self.rank + 1) / self.among_nb_days)
        return f'Top {top}%.'


def _month_to_french(month: Month) -> str:
    return f'{month_to_french_word(month.month)} {month.year}'


def _build_french_ordinal(rank: int) -> str:
    if rank == 0:
        return ''
    return f'{rank + 1}ème '


@dataclass
class MonthSummaryEvent:
    month: Month
    month_count: int
    month_rank: int

    @staticmethod
    def default_score() -> float:
        return 0.95

    def default_message(self) -> str:
        month_name = _month_to_french(self.month)
        french_ordinal = _build_french_ordinal(self.month_rank)
        return f'{month_name} : {french_ordinal}meilleur mois de l\'histoire avec {self.month_count} passages.'


@dataclass
class YearSummaryEvent:
    year: int
    year_count: int
    year_rank: int

    @staticmethod
    def default_score() -> float:
        return 0.96

    def default_message(self) -> str:
        french_ordinal = _build_french_ordinal(self.year_rank)
        return f'{self.year} : {french_ordinal}meilleure année de l\'histoire avec {self.year_count} passages.'


@dataclass
class YearTotalEvent:
    year_total: int
    day: date

    def default_score(self) -> float:
        if self.day.day == 1:
            return 0
        if self.day.day <= 4:
            return 0.4
        if _number_is_funny(self.year_total):
            return 0.75
        return 0.5

    def default_message(self) -> str:
        return f'{self.year_total} passages depuis le début de l\'année.'


@dataclass
class MonthTotalEvent:
    month_total: int
    day: date

    def default_score(self) -> float:
        if self.day.day == 1:
            return 0
        if _number_is_funny(self.month_total):
            return 0.75
        if self.day.day <= 4:
            return 0.4
        return 0.5

    def default_message(self) -> str:
        return f'{self.month_total} passages depuis le début du mois.'


@dataclass
class HistoricalTotalEvent:
    historical_total: int

    def default_score(self) -> float:
        if _number_is_funny(self.historical_total):
            return 0.75
        return 0.5

    def default_message(self) -> str:
        return f'{self.historical_total} passages depuis l\'installation du compteur.'


Event = Union[
    MonthRecordEvent,
    HistoricalRecordEvent,
    DayHistoricalRankEvent,
    MonthSummaryEvent,
    YearSummaryEvent,
    YearTotalEvent,
    MonthTotalEvent,
    HistoricalTotalEvent,
]


def _get_month_to_count(count_history: CountHistory) -> Dict[Month, int]:
    month_to_counts = _group_by_month(count_history)
    return {month: sum(counts) for month, counts in month_to_counts.items()}


def _extract_month_event(day: date, count_history: CountHistory) -> MonthSummaryEvent:
    month_to_count = _get_month_to_count(count_history)
    month = _get_month(day)
    rank = _optimistic_rank(month_to_count[month], month_to_count.values())
    return MonthSummaryEvent(month, month_to_count[month], rank)


def _get_year_to_count(count_history: CountHistory) -> Dict[int, int]:
    month_to_counts = _group_by_year(count_history)
    return {month: sum(counts) for month, counts in month_to_counts.items()}


def _extract_year_event(day: date, count_history: CountHistory) -> YearSummaryEvent:
    year_to_count = _get_year_to_count(count_history)
    rank = _optimistic_rank(year_to_count[day.year], year_to_count.values())
    return YearSummaryEvent(day.year, year_to_count[day.year], rank)


EventComputer = Callable[[date, CountHistory], Optional[Event]]


# EVENT COMPUTERS TODO: MOVE
def _historical_record(day: date, count_history: CountHistory) -> Optional[HistoricalRecordEvent]:
    if _day_is_absolute_maximum(day, count_history):
        return HistoricalRecordEvent()
    return None


def _get_day_rank(day: date, count_history: CountHistory) -> DayHistoricalRankEvent:
    historical_rank = _day_rank(day, count_history)
    return DayHistoricalRankEvent(historical_rank, len(count_history.daily_counts))


def _get_month_summary(day: date, count_history: CountHistory) -> Optional[MonthSummaryEvent]:
    if _day_is_last_day_of_month(day):
        return _extract_month_event(day, count_history)
    return None


def _get_year_summary(day: date, count_history: CountHistory) -> Optional[YearSummaryEvent]:
    if _day_is_last_day_of_year(day):
        return _extract_year_event(day, count_history)
    return None


def _extract_total_count_event(day: date, count_history: CountHistory) -> HistoricalTotalEvent:
    del day  # hack for linter
    total = sum(count_history.day_to_count.values())
    return HistoricalTotalEvent(total)


def _extract_month_total_count_event(day: date, count_history: CountHistory) -> MonthTotalEvent:
    month_to_count = _get_month_to_count(count_history)
    month = _get_month(day)
    return MonthTotalEvent(month_to_count[month], day)


def _extract_year_total_count_event(day: date, count_history: CountHistory) -> YearTotalEvent:
    year_to_count = _get_year_to_count(count_history)
    year = day.year
    return YearTotalEvent(year_to_count[year], day)


_EVENT_COMPUTERS: List[EventComputer] = [
    _historical_record,
    _get_day_rank,
    _get_month_summary,
    _get_year_summary,
    _extract_total_count_event,
    _extract_month_total_count_event,
    _extract_year_total_count_event,
]


# TODO: Week Rank, rank in week, ...
def _extract_counting_events(
    day: date, count_history: CountHistory, event_computers: List[EventComputer]
) -> List[Event]:
    potential_events = [event_computer(day, count_history) for event_computer in event_computers]
    return [event for event in potential_events if event]


def _randomly_choose_index_among_max_values(values: List[float]) -> int:
    if not values:
        raise ValueError('Need at least one value to get biggest one.')
    max_value = max(values)
    return random.choice([i for i, value in enumerate(values) if value == max_value])


def _score_event(event: Event) -> float:
    return event.default_score()


def _elect_event(events: List[Event]) -> Event:
    if not events:
        raise ValueError('Need at least one event to choose one.')
    event_scores = [_score_event(event) for event in events]
    return events[_randomly_choose_index_among_max_values(event_scores)]


def _remove_posterior_days(day: date, count_history: CountHistory) -> CountHistory:
    return CountHistory([cnt for cnt in count_history.daily_counts if cnt.date <= day])


def _compute_most_interesting_fact(day: date, count_history: CountHistory) -> Event:
    truncated_count_history = _remove_posterior_days(day, count_history)
    events = _extract_counting_events(day, truncated_count_history, _EVENT_COMPUTERS)
    return _elect_event(events)


def _compute_day_expression(day: date, publish_date: date) -> str:
    if day == publish_date:
        return 'Aujourd\'hui'
    if publish_date - timedelta(days=1) == day:
        return 'Hier'
    date_str = date_to_dmy(day)
    return f'Le {date_str}'


def _compute_first_half_of_tweet(day: date, count_history: CountHistory, publish_date: date) -> str:
    day_expression = _compute_day_expression(day, publish_date)
    nb_occurrences_this_day = _safe_get_count(day, count_history)
    return f'{day_expression}, il y a eu {nb_occurrences_this_day} cyclistes.'


def _event_to_fact(event: Event) -> str:
    return event.default_message()


def build_tweet(day: date, count_history: CountHistory, publish_date: date, hashtag: Optional[Hashtag]) -> Tweet:
    event = _compute_most_interesting_fact(day, count_history)
    tweet_lines = [_compute_first_half_of_tweet(day, count_history, publish_date), _event_to_fact(event)]
    if hashtag:
        tweet_lines.append(hashtag.content)
    return Tweet('\n'.join(tweet_lines))


# TODO: tests e2e
# TODO: fetch_data template
# TODO: Readme.md
# TODO: docstring
# TODO: precommit
# TODO: github cicd for tests
