from typing import Dict, Set, List, Tuple, Optional, TypeVar, Union
from datetime import datetime, timedelta
from collections import Counter

import json
import logging
import traceback
import requests

from rivoli.config import get_twitter, ECO_COUNTER_URL
from rivoli.exceptions import FailedRequestingEcoCounterError, PublishError
from rivoli.utils import parse_mdy

MAX_TWEET_LENGTH = 280


class Publisher:
    def publish(self, message: str) -> None:
        raise NotImplementedError()

    def can_be_published(self, message: str) -> bool:
        raise NotImplementedError()


class TweetPublisher(Publisher):
    def publish(self, message: str) -> None:
        if not self.can_be_published(message):
            raise PublishError(f'Cannot publish tweet {message}.')
        twitter_api = get_twitter()
        twitter_api.update_status(message)

    def can_be_published(self, message: str) -> bool:
        return len(message) <= MAX_TWEET_LENGTH


class SlackPublisher(Publisher):
    def __init__(self, slack_url: str) -> None:
        self.slack_url: str = slack_url

    def publish(self, message: str) -> None:
        if not self.can_be_published(message):
            raise PublishError(f'Cannot publish message {message} to slack.')
        requests.post(url=self.slack_url, data=json.dumps({'text': message}))

    def can_be_published(self, message: str) -> bool:
        return True


class TimeRange:
    start_date: datetime

    def contains(self, date: datetime) -> bool:
        raise NotImplementedError

    @staticmethod
    def check(date: datetime) -> None:
        raise NotImplementedError


class MonthTimeRange(TimeRange):
    def __init__(self, start_date: datetime) -> None:
        self.check(start_date)
        self.start_date = start_date

    def contains(self, date: datetime) -> bool:
        return self.start_date.year == date.year and self.start_date.month == date.month

    @staticmethod
    def check(date: datetime) -> None:
        DayTimeRange.check(date)
        if date.day != 1:
            raise ValueError(f'Date {date} is not a month')


class YearTimeRange(TimeRange):
    def __init__(self, start_date: datetime) -> None:
        self.check(start_date)
        self.start_date = start_date

    def contains(self, date: datetime) -> bool:
        return self.start_date.year == date.year

    @staticmethod
    def check(date: datetime) -> None:
        MonthTimeRange.check(date)
        if date.month != 1:
            raise ValueError(f'Date {date} is not a year')


class HistoricalTimeRange(CustomTimeRange):
    pass


class DayTimeRange(TimeRange):
    def __init__(self, start_date: datetime) -> None:
        self.check(start_date)
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=1)

    def contains(self, date: datetime) -> bool:
        return self.start_date <= date < self.end_date

    def month_time_range(self) -> MonthTimeRange:
        first_day_of_month = datetime(year=self.start_date.year, month=self.start_date.month, day=1)
        return MonthTimeRange(first_day_of_month)

    def year_time_range(self) -> YearTimeRange:
        first_day_of_year = datetime(year=self.start_date.year, month=1, day=1)
        return YearTimeRange(first_day_of_year)

    def day_of_week(self) -> str:
        return DayOfWeek.from_int(self.start_date.weekday())

    @staticmethod
    def check(date: datetime) -> None:
        if date.hour != 0 or date.minute != 0 or date.second != 0:
            raise ValueError(f'Date {date} is not a day')


class HourTimeRange(TimeRange):
    def __init__(self, start_date: datetime) -> None:
        self.check(start_date)
        self.start_date = start_date
        self.end_date = start_date + timedelta(hours=1)

    def contains(self, date: datetime) -> bool:
        return self.start_date <= date < self.end_date

    def hour(self) -> int:
        return self.start_date.hour

    def day_of_week(self) -> str:
        return DayOfWeek.from_int(self.start_date.weekday())

    def day_time_range(self) -> DayTimeRange:
        day = datetime(year=self.start_date.year, month=self.start_date.month, day=self.start_date.day)
        return DayTimeRange(day)

    @staticmethod
    def check(date: datetime) -> None:
        if date.minute != 0 or date.second != 0:
            raise ValueError(f'Date {date} is not an hour')


class CustomTimeRange(TimeRange):
    def __init__(self, start_date: datetime, end_date: datetime) -> None:
        self.start_date = start_date
        self.end_date = end_date

    def contains(self, date: datetime) -> bool:
        return self.start_date <= date < self.end_date

    @staticmethod
    def check(date: datetime) -> None:
        pass


class Language:
    FR = 'fr'
    EN = 'en'

    @staticmethod
    def values() -> Set[str]:
        return {Language.FR, Language.EN}


class Dictionary:
    def __init__(self, key_to_language_to_sentence: Dict[str, Dict[str, str]]) -> None:
        self.key_to_language_to_sentence: Dict[str, Dict[str, str]] = key_to_language_to_sentence

    def __getitem__(self, key: str):
        return self.key_to_language_to_sentence[key]

    def to_json(self) -> Dict:
        return self.key_to_language_to_sentence

    @classmethod
    def from_json(cls, json_dictionary: Dict[str, Dict[str, str]]):
        is_ok, message = cls.check_json(json_dictionary)
        if not is_ok:
            raise ValueError(message)
        return cls(key_to_language_to_sentence=json_dictionary)

    @staticmethod
    def check_json(json_dictionary: Dict[str, Dict[str, str]]) -> Tuple[bool, str]:
        if isinstance(json_dictionary, dict):
            return False, 'json_dictionary must be of type dict'
        return True, ''


class CountHistoryType:
    HOURLY_COUNT = 'HOURLY_COUNT'
    DAILY_COUNT = 'DAILY_COUNT'


T_ = TypeVar('T_', bound=TimeRange)


class DailyCountHistory:
    def __init__(self, day_to_count: Dict[DayTimeRange, int]) -> None:

        self.day_to_count: Dict[DayTimeRange, int] = day_to_count

        self.month_to_count: Dict[MonthTimeRange, int] = self._group_by_month(day_to_count)
        self.year_to_count: Dict[YearTimeRange, int] = self._group_by_year(day_to_count)
        self.total: int = sum(self.day_to_count.values())
        self.day_to_cumsum: Dict[DayTimeRange, int] = self._time_range_to_cumsum(day_to_count)
        self.month_to_cumsum: Dict[MonthTimeRange, int] = self._time_range_to_cumsum(self.month_to_count)
        self.day_of_week_to_best_count: Dict[str, int] = self._extract_day_of_week_to_best_count(day_to_count)

    @staticmethod
    def _group_by_month(day_to_count: Dict[DayTimeRange, int]) -> Dict[MonthTimeRange, int]:
        month_to_day_counts: Dict[MonthTimeRange, List[int]] = {}
        for day, count in day_to_count.items():
            month = day.month_time_range()
            month_to_day_counts[month] = month_to_day_counts.get(month, []) + [count]
        return {month: sum(counts) for month, counts in month_to_day_counts.items()}

    @staticmethod
    def _group_by_year(day_to_count: Dict[DayTimeRange, int]) -> Dict[YearTimeRange, int]:
        year_to_day_counts: Dict[YearTimeRange, List[int]] = {}
        for day, count in day_to_count.items():
            year = day.year_time_range()
            year_to_day_counts[year] = year_to_day_counts.get(year, []) + [count]
        return {year: sum(counts) for year, counts in year_to_day_counts.items()}

    @staticmethod
    def _time_range_to_cumsum(time_range_to_count: Dict[T_, int]) -> Dict[T_, int]:
        time_range_to_cumsum = {}
        cumsum = 0
        for key, count in sorted(time_range_to_count.items(), key=lambda x: x[0].start_date):
            cumsum += count
            time_range_to_cumsum[key] = cumsum
        return time_range_to_cumsum

    @staticmethod
    def _extract_day_of_week_to_best_count(day_to_count: Dict[DayTimeRange, int]) -> Dict[str, int]:
        day_of_week_to_day_counts: Dict[str, List[int]] = {}
        for day, count in day_to_count.items():
            day_of_week = day.day_of_week()
            day_of_week_to_day_counts[day_of_week] = day_of_week_to_day_counts.get(day_of_week, []) + [count]
        return {day_of_week: max(counts) for day_of_week, counts in day_of_week_to_day_counts.items()}


class HourlyCountHistory(DailyCountHistory):
    def __init__(self, hour_to_count: Dict[HourTimeRange, int]) -> None:
        day_to_count = self._group_by_day(hour_to_count)
        super().__init__(day_to_count)

        self.hour_to_count: Optional[Dict[HourTimeRange, int]] = hour_to_count
        self.hour_to_cumsum: Dict[HourTimeRange, int] = self._time_range_to_cumsum(hour_to_count)
        self.hour_and_day_of_week_to_best_count: Dict[
            Tuple[int, str], int
        ] = self._extract_hour_and_day_of_week_to_best_count(hour_to_count)

    @staticmethod
    def _extract_hour_and_day_of_week_to_best_count(
        hour_to_count: Dict[HourTimeRange, int]
    ) -> Dict[Tuple[int, str], int]:
        hour_and_day_of_week_to_counts: Dict[Tuple[int, str], List[int]] = {}
        for hour, count in hour_to_count.items():
            key = (hour.hour(), hour.day_of_week())
            hour_and_day_of_week_to_counts[key] = hour_and_day_of_week_to_counts.get(key, []) + [count]
        return {key: max(counts) for key, counts in hour_and_day_of_week_to_counts.items()}

    @staticmethod
    def _group_by_day(hour_to_count: Dict[HourTimeRange, int]) -> Dict[DayTimeRange, int]:
        day_to_hour_counts: Dict[DayTimeRange, List[int]] = {}
        for hour, count in hour_to_count.items():
            day = hour.day_time_range()
            day_to_hour_counts[day] = day_to_hour_counts.get(day, []) + [count]
        return {day: sum(counts) for day, counts in day_to_hour_counts.items()}


class CountHistoryDownloader:
    def download_count_history(self) -> DailyCountHistory:
        raise NotImplementedError


class EcoCounterDownloader(CountHistoryDownloader):
    def download_count_history(self) -> DailyCountHistory:
        try:
            answer = requests.post(ECO_COUNTER_URL)
            if answer.status_code != 200:
                json_answer = answer.json()
        except Exception:
            logging.error(traceback.format_exc())
            raise FailedRequestingEcoCounterError()
        return self._format_answer(json_answer)

    @classmethod
    def _check_answer(cls, answer: List) -> Tuple[bool, str]:
        if not isinstance(answer, list):
            return False, f'Expected API answer type is list, received {type(answer)}'
        if not answer[0][0] != '09/02/2019':
            return False, f'Expected first day of data: 09/02/2019. Received {answer[0][0]}'
        pairs = answer[:-1]
        if {len(pair) for pair in pairs} != {2}:
            return (
                False,
                'Expecting a list of pairs, lengths received: {}'.format(
                    Counter([len(pair) for pair in pairs]).most_common()
                ),
            )
        return True, ''

    @classmethod
    def _format_pair(cls, pair: Tuple[str, str]) -> Tuple[DayTimeRange, int]:
        if len(pair) != 2:
            raise ValueError('Need a pair as argument, received {}'.format(pair))
        date = parse_mdy(pair[0])
        time_range = DayTimeRange(start_date=date)
        count = int(float(pair[1]))
        return time_range, count

    @staticmethod
    def _pad_answer(answer):
        return [['09/01/2019', '0']] + answer

    @classmethod
    def _format_answer(cls, answer: List[Tuple[str, str]]) -> DailyCountHistory:
        is_ok, message = cls._check_answer(answer)
        if not is_ok:
            raise ValueError(f'Cannot build count history from url answer, reason: {message}')
        padded_answer = cls._pad_answer(answer)
        day_to_count = dict([cls._format_pair(pair) for pair in padded_answer[:-1]])
        return DailyCountHistory(day_to_count=day_to_count)


class DayOfWeek:  # (Enum) {
    MONDAY = 'MONDAY'
    TUESDAY = 'TUESDAY'
    WEDNESDAY = 'WEDNESDAY'
    THURSDAY = 'THURSDAY'
    FRIDAY = 'FRIDAY'
    SATURDAY = 'SATURDAY'
    SUNDAY = 'SUNDAY'

    @classmethod
    def from_int(cls, int_: int):
        return {
            0: cls.MONDAY,
            1: cls.TUESDAY,
            2: cls.WEDNESDAY,
            3: cls.THURSDAY,
            4: cls.FRIDAY,
            5: cls.SATURDAY,
            6: cls.SUNDAY,
        }[int_]


class RelevantFactType:
    BEST_HOUR_IN_DAY = 'BEST_HOUR_IN_DAY'

    HISTORICAL_RANK_OF_BEST_HOUR = 'HISTORICAL_RANK_OF_BEST_HOUR'
    YEAR_RANK_OF_BEST_HOUR = 'YEAR_RANK_OF_BEST_HOUR'
    MONTH_RANK_OF_BEST_HOUR = 'MONTH_RANK_OF_BEST_HOUR'

    HISTORICAL_RANK_OF_DAY_OF_WEEK = 'HISTORICAL_RANK_OF_DAY_OF_WEEK'
    YEAR_RANK_OF_DAY_OF_WEEK = 'YEAR_RANK_OF_DAY_OF_WEEK'
    MONTH_RANK_OF_DAY_OF_WEEK = 'MONTH_RANK_OF_DAY_OF_WEEK'

    HISTORICAL_TOTAL = 'HISTORICAL_TOTAL'
    YEAR_TOTAL = 'YEAR_TOTAL'
    MONTH_TOTAL = 'MONTH_TOTAL'

    RANK_OF_YEAR_TOTAL = 'RANK_OF_YEAR_TOTAL'
    RANK_OF_MONTH_TOTAL = 'RANK_OF_MONTH_TOTAL'

    INTERESTING_HISTORICAL_TOTAL = 'INTERESTING_HISTORICAL_TOTAL'
    INTERESTING_YEAR_TOTAL = 'INTERESTING_YEAR_TOTAL'
    INTERESTING_MONTH_TOTAL = 'INTERESTING_MONTH_TOTAL'

    TOTAL_AVOIDED_CARBON = 'TOTAL_AVOIDED_CARBON'

    # multiple counter
    BEST_OTHER_COUNTER_DAY = 'BEST_OTHER_COUNTER_DAY'
    RANK_OF_COUNTER_AMONG_OTHER_COUNTERS = 'RANK_OF_COUNTER_AMONG_OTHER_COUNTERS'
    BEST_HOUR_AMONG_ALL_COUNTERS = 'BEST_HOUR_AMONG_ALL_COUNTERS'

    # compared to day qualifiers
    HISTORICAL_RANK_FOR_RAINY_DAYS = 'HISTORICAL_RANK_FOR_RAINY_DAYS'
    HISTORICAL_RANK_FOR_TEMPERATURE_OR_BELOW = 'HISTORICAL_RANK_FOR_TEMPERATURE_OR_BELOW'

    # machine learning
    PREDICTED_NUMBER_OF_CYCLISTS_FOR_THE_DAY = 'PREDICTED_NUMBER_OF_CYCLISTS_FOR_THE_DAY'


class RelevantFact:
    # type: str

    def __init__(self, target_range: TimeRange, among_range: TimeRange, priority: int) -> None:
        self.target_range: TimeRange = target_range
        self.among_range: TimeRange = among_range
        self.priority: int = priority

    def to_string(self, language: str, day_of_publication: datetime, dictionary: Dictionary) -> str:
        raise NotImplementedError


class DictionaryKeys:
    HISTORICAL_TOTAL = 'HISTORICAL_TOTAL'
    YEAR_TOTAL = 'YEAR_TOTAL'
    MONTH_TOTAL = 'MONTH_TOTAL'
    FIRST = 'FIRST'
    SECOND = 'SECOND'
    THIRD = 'THIRD'
    ITH = 'ITH'
    FEMALE_BEST = 'FEMALE_BEST'
    MALE_BEST = 'MALE_BEST'
    MONDAY = 'MONDAY'
    TUESDAY = 'TUESDAY'
    WEDNESDAY = 'WEDNESDAY'
    THURSDAY = 'THURSDAY'
    FRIDAY = 'FRIDAY'
    SATURDAY = 'SATURDAY'
    SUNDAY = 'SUNDAY'
    SINCE_BEGINING = 'SINCE_BEGINING'
    SINCE_BEGINING_OF_YEAR = 'SINCE_BEGINING_OF_YEAR'
    SINCE_BEGINING_OF_MONTH = 'SINCE_BEGINING_OF_MONTH'
    DAY_OF_MONTH = 'DAY_OF_MONTH'
    DAY_OF_YEAR = 'DAY_OF_YEAR'
    DAY_OF_HISTORY = 'DAY_OF_HISTORY'
    MONTH_OF_YEAR = 'MONTH_OF_YEAR'
    MONTH_OF_HISTORY = 'MONTH_OF_HISTORY'
    YEAR_OF_HISTORY = 'YEAR_OF_HISTORY'


def day_of_week_to_name(day_of_week: str, language: str, dictionary: Dictionary):
    return dictionary[day_of_week][language]


def rank_to_ordinal(rank: int, language: str, dictionary: Dictionary) -> str:
    if rank == 0:
        return dictionary[DictionaryKeys.FIRST][language]
    if rank == 1:
        return dictionary[DictionaryKeys.SECOND][language]
    if rank == 2:
        return dictionary[DictionaryKeys.THIRD][language]
    return f'{rank}{dictionary[DictionaryKeys.ITH][Language]}'


class TotalRelevantFact(RelevantFact):
    def __init__(self, target_range: TimeRange, among_range: TimeRange, priority: int, total: int) -> None:
        super().__init__(target_range, among_range, priority)
        self.total: int = total

    @staticmethod
    def end_of_sentence(language: str, dictionary: Dictionary) -> str:
        raise NotImplementedError()

    def to_string(self, language: str, day_of_publication: datetime, dictionary: Dictionary) -> str:
        return f'{self.total} {self.end_of_sentence( language, dictionary)}.'


class HistoricalTotalRelevantFact(TotalRelevantFact):
    @staticmethod
    def end_of_sentence(language: str, dictionary: Dictionary) -> str:
        return dictionary[DictionaryKeys.HISTORICAL_TOTAL]


class YearTotalRelevantFact(TotalRelevantFact):
    @staticmethod
    def end_of_sentence(language: str, dictionary: Dictionary) -> str:
        return dictionary[DictionaryKeys.YEAR_TOTAL]


class MonthTotalRelevantFact(TotalRelevantFact):
    @staticmethod
    def end_of_sentence(language: str, dictionary: Dictionary) -> str:
        return dictionary[DictionaryKeys.MONTH_TOTAL]


class RankOfTotalRelevantFact(RelevantFact):
    def __init__(
        self, target_range: TimeRange, among_range: TimeRange, priority: int, total: int, rank_of_total: int
    ) -> None:
        super().__init__(target_range, among_range, priority)
        self.total: int = total
        self.rank: int = rank_of_total

    @staticmethod
    def _get_best(rank: int, language: str, dictionary: Dictionary) -> str:
        raise NotImplementedError()

    @staticmethod
    def _get_rank_end_of_sentence(
        target_range: TimeRange, among_range: TimeRange, language: str, dictionary: Dictionary
    ) -> str:
        if isinstance(target_range, DayTimeRange) and isinstance(among_range, MonthTimeRange):
            return dictionary[DictionaryKeys.DAY_OF_MONTH][language]
        if isinstance(target_range, DayTimeRange) and isinstance(among_range, YearTimeRange):
            return dictionary[DictionaryKeys.DAY_OF_YEAR][language]
        if isinstance(target_range, DayTimeRange) and isinstance(among_range, HistoricalTimeRange):
            return dictionary[DictionaryKeys.DAY_OF_HISTORY][language]
        if isinstance(target_range, MonthTimeRange) and isinstance(among_range, YearTimeRange):
            return dictionary[DictionaryKeys.MONTH_OF_YEAR][language]
        if isinstance(target_range, MonthTimeRange) and isinstance(among_range, HistoricalTimeRange):
            return dictionary[DictionaryKeys.MONTH_OF_HISTORY][language]
        if isinstance(target_range, YearTimeRange) and isinstance(among_range, HistoricalTimeRange):
            return dictionary[DictionaryKeys.YEAR_OF_HISTORY][language]
        raise NotImplementedError()

    def to_string(self, language: str, day_of_publication: datetime, dictionary: Dictionary) -> str:
        best = self._get_best(self.rank, language, dictionary)
        end_of_sentence = self._get_rank_end_of_sentence(self.target_range, self.among_range, language, dictionary)
        string_time_range = self.time_range.to_string(language, dictionary)
        return f'{string_time_range}: {best} {end_of_sentence}'


class DayOfMonthRankOfTotalRelevantFact(RankOfTotalRelevantFact):
    @staticmethod
    def _get_best(rank: int, language: str, dictionary: Dictionary) -> str:
        return get_male_best(rank, language, dictionary)


class DayOfYearRankOfTotalRelevantFact(RankOfTotalRelevantFact):
    @staticmethod
    def _get_best(rank: int, language: str, dictionary: Dictionary) -> str:
        return get_male_best(rank, language, dictionary)


class DayOfHistoricalRankOfTotalRelevantFact(RankOfTotalRelevantFact):
    @staticmethod
    def _get_best(rank: int, language: str, dictionary: Dictionary) -> str:
        return get_male_best(rank, language, dictionary)


class MonthOfYearRankOfTotalRelevantFact(RankOfTotalRelevantFact):
    @staticmethod
    def _get_best(rank: int, language: str, dictionary: Dictionary) -> str:
        return get_male_best(rank, language, dictionary)


class MonthOfHistoryRankOfTotalRelevantFact(RankOfTotalRelevantFact):
    @staticmethod
    def _get_best(rank: int, language: str, dictionary: Dictionary) -> str:
        return get_female_best(rank, language, dictionary)


class YearOfHistoryRankOfTotalRelevantFact(RankOfTotalRelevantFact):
    @staticmethod
    def _get_best(rank: int, language: str, dictionary: Dictionary) -> str:
        return get_male_best(rank, language, dictionary)


def get_male_best(rank: int, language: str, dictionary: Dictionary) -> str:
    ordinal = rank_to_ordinal(rank, language, dictionary)
    best = dictionary[DictionaryKeys.MALE_BEST][language]
    ordinal_best = f'{ordinal} {best}' if rank else best
    return ordinal_best


def get_female_best(rank: int, language: str, dictionary: Dictionary) -> str:
    ordinal = rank_to_ordinal(rank, language, dictionary)
    best = dictionary[DictionaryKeys.FEMALE_BEST][language]
    ordinal_best = f'{ordinal} {best}' if rank else best
    return ordinal_best


def get_male_best_day_of_week_sentence(rank: int, day_of_week: str, language: str, dictionary: Dictionary) -> str:
    day_of_week_name = day_of_week_to_name(day_of_week, language, dictionary)
    return f'{get_male_best(rank, language, dictionary)} {day_of_week_name}'


class DayOfWeekRankRelevantFact(RelevantFact):
    def __init__(
        self, target_range: TimeRange, among_range: TimeRange, priority: int, rank: int, day_of_week: str
    ) -> None:
        super().__init__(target_range, among_range, priority)
        if not isinstance(among_range, DayTimeRange):
            raise ValueError('DayOfWeekRankRelevantFact can only be computed for days.')
        self.rank: int = rank
        self.day_of_week: str = day_of_week

    @staticmethod
    def get_end_of_sentence(language: str, dictionary: Dictionary) -> str:
        raise NotImplementedError()

    def to_string(self, language: str, day_of_publication: datetime, dictionary: Dictionary) -> str:
        best_day_of_week_sentence = get_male_best_day_of_week_sentence(
            self.rank, self.day_of_week, language, dictionary
        )
        return f'{best_day_of_week_sentence} {self.get_end_of_sentence(language, dictionary)}.'


class HistoricalDayOfWeekRankRelevantFact(DayOfWeekRankRelevantFact):
    # type: str = RelevantFactType.HISTORICAL_RANK_OF_DAY_OF_WEEK

    @staticmethod
    def get_end_of_sentence(language: str, dictionary: Dictionary) -> str:
        return dictionary[DictionaryKeys.SINCE_BEGINING][language]


class YearDayOfWeekRankRelevantFact(DayOfWeekRankRelevantFact):
    # type: str = RelevantFactType.YEAR_RANK_OF_DAY_OF_WEEK

    @staticmethod
    def get_end_of_sentence(language: str, dictionary: Dictionary) -> str:
        return dictionary[DictionaryKeys.SINCE_BEGINING_OF_YEAR][language]


class MonthDayOfWeekRankRelevantFact(DayOfWeekRankRelevantFact):
    # type: str = RelevantFactType.MONTH_RANK_OF_DAY_OF_WEEK

    @staticmethod
    def get_end_of_sentence(language: str, dictionary: Dictionary) -> str:
        return dictionary[DictionaryKeys.SINCE_BEGINING_OF_MONTH][language]


def extract_relevant_facts(
    count_history: DailyCountHistory, among_range: TimeRange, target_range: Union[DayTimeRange, HourTimeRange]
) -> List[RelevantFact]:
    # if not among_range.contains(target_range):
    #     raise ValueError('Arg among_range must contain arg target_range')
    # HistoricalTotalRelevantFact(time_range, among_range, RelevantFactType.HISTORICAL_TOTAL)

    if isinstance(count_history, HourlyCountHistory):
        pass  # TODO


def relevant_facts_to_string(
    relevant_facts: List[RelevantFact], language: Language, time_of_publication: datetime
) -> str:
    NotImplemented
