from dataclasses import dataclass, asdict, field
from datetime import date, timedelta
from typing import Any, Dict, List
from rivoli.utils import date_to_ymd, parse_ymd


@dataclass
class DayCount:
    date: date
    count: int

    @staticmethod
    def from_json(dict_: Dict[str, Any]) -> 'DayCount':
        dict_ = dict_.copy()
        dict_['date'] = parse_ymd(dict_['date'])
        return DayCount(**dict_)

    def to_json(self) -> Dict[str, Any]:
        res = asdict(self)
        res['date'] = date_to_ymd(self.date)
        return res

    def to_csv(self) -> str:
        return f'{date_to_ymd(self.date)},{self.count}'

    @staticmethod
    def from_csv(str_: str) -> 'DayCount':
        date_str, count_str = str_.split(',')
        return DayCount(parse_ymd(date_str), int(count_str))


def _check_continuous_and_increasing(days: List[DayCount]) -> None:
    for day, day_after in zip(days, days[1:]):
        if day.date != day_after.date - timedelta(1):
            raise ValueError(f'Counter not increasing and continuous: {day.date} and {day_after.date} are consecutive')


@dataclass
class CountHistory:
    daily_counts: List[DayCount]
    day_to_count: Dict[date, int] = field(init=False)

    def __post_init__(self):
        _check_continuous_and_increasing(self.daily_counts)
        self.day_to_count = {count.date: count.count for count in self.daily_counts}

    @staticmethod
    def from_json(dict_: Dict[str, Any]) -> 'CountHistory':
        return CountHistory([DayCount.from_json(x) for x in dict_['daily_counts']])

    def to_json(self) -> Dict[str, Any]:
        return {'daily_counts': [x.to_json() for x in self.daily_counts]}

    def to_csv(self) -> str:
        return '\n'.join([count.to_csv() for count in self.daily_counts])

    @staticmethod
    def from_csv(str_: str) -> 'CountHistory':
        return CountHistory([DayCount.from_csv(x) for x in str_.split('\n')])


@dataclass(frozen=True, eq=True)
class Month:
    month: int
    year: int


@dataclass
class Tweet:
    content: str

    def __post_init__(self):
        if len(self.content) > 280:
            raise ValueError('Tweet content must contain less than 280 characters.')


@dataclass
class Hashtag:
    content: str

    def __post_init__(self):
        if not self.content or self.content[0] != '#':
            raise ValueError(f'Expecting hastag to start with char #. Received {self.content}')
