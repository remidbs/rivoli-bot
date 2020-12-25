import os
from rivoli.utils import parse_ymd
from rivoli.models import CountHistory, DayCount, Month
import pytest
from datetime import date, timedelta

from rivoli.app_v3 import (
    _cumulate,
    _day_is_absolute_maximum,
    _day_is_first_day_of_month,
    _day_is_first_day_of_year,
    _day_is_last_day_of_month,
    _day_is_monthly_record,
    _day_is_year_maximum,
    _day_rank,
    _extract_total_count,
    _get_month,
    _get_month_range,
    _group_by_month,
    _group_by_year,
    _month_to_cumulate_sums,
    _number_is_funny,
    _optimistic_rank,
    _safe_get_count,
    day_is_today,
    day_is_yesterday,
)


def test_day_is_today():
    assert day_is_today(date.today())
    assert not day_is_today(date.today() + timedelta(days=1))
    assert not day_is_today(date.today() + timedelta(days=365))
    assert not day_is_today(date.today() - timedelta(days=366))


def test_day_is_yesterday():
    assert not day_is_yesterday(date.today())
    assert not day_is_yesterday(date.today() + timedelta(days=1))
    assert not day_is_yesterday(date.today() + timedelta(days=365))
    assert not day_is_yesterday(date.today() - timedelta(days=366))
    assert day_is_yesterday(date.today() - timedelta(days=1))


def test_safe_get_count():
    with pytest.raises(ValueError):
        _safe_get_count(date.today(), CountHistory([]))
        _safe_get_count(date.today(), CountHistory([DayCount(date.today() + timedelta(1), 1)]))
    assert _safe_get_count(date.today(), CountHistory([DayCount(date.today(), 1)]))


_COUNT_HISTORY_CSV = '''2020/08/31,100
2020/09/01,200
2020/09/02,350
2020/09/03,250
2020/09/04,50
2020/09/05,120'''


def _get_small_count_history() -> CountHistory:
    return CountHistory.from_csv(_COUNT_HISTORY_CSV)


def _get_folder() -> str:
    return '/'.join(__file__.split('/')[:-1])


def _get_rivoli_test_count_history() -> CountHistory:
    return CountHistory.from_csv(open(os.path.join(_get_folder(), 'test_data', 'rivoli_test_data.csv')).read())


def test_day_is_absolute_maximum():
    count_history = _get_small_count_history()
    assert _day_is_absolute_maximum(parse_ymd('2020/09/02'), count_history)
    assert not _day_is_absolute_maximum(parse_ymd('2020/09/03'), count_history)
    assert not _day_is_absolute_maximum(parse_ymd('2020/09/04'), count_history)
    assert not _day_is_absolute_maximum(parse_ymd('2020/09/05'), count_history)

    count_history = _get_rivoli_test_count_history()
    assert not _day_is_absolute_maximum(parse_ymd('2020/09/03'), count_history)
    assert not _day_is_absolute_maximum(parse_ymd('2020/09/04'), count_history)
    assert not _day_is_absolute_maximum(parse_ymd('2020/09/05'), count_history)
    assert not _day_is_absolute_maximum(parse_ymd('2020/12/05'), count_history)


def test_day_is_year_maximum():
    assert _day_is_year_maximum(date.today(), CountHistory([DayCount(date.today(), 10)]))
    assert not _day_is_year_maximum(date(2020, 8, 31), _get_small_count_history())
    assert not _day_is_year_maximum(date(2020, 9, 1), _get_small_count_history())
    assert _day_is_year_maximum(date(2020, 9, 2), _get_small_count_history())
    assert not _day_is_year_maximum(date(2020, 9, 3), _get_small_count_history())
    assert not _day_is_year_maximum(date(2020, 9, 4), _get_small_count_history())
    assert not _day_is_year_maximum(date(2020, 9, 5), _get_small_count_history())
    assert not _day_is_year_maximum(date(2020, 9, 3), _get_rivoli_test_count_history())
    assert not _day_is_year_maximum(date(2020, 9, 4), _get_rivoli_test_count_history())


def test_day_is_monthly_record():
    assert _day_is_monthly_record(date.today(), CountHistory([DayCount(date.today(), 10)]))
    assert _day_is_monthly_record(date(2020, 8, 31), _get_small_count_history())
    assert not _day_is_monthly_record(date(2020, 9, 1), _get_small_count_history())
    assert _day_is_monthly_record(date(2020, 9, 2), _get_small_count_history())
    assert not _day_is_monthly_record(date(2020, 9, 3), _get_small_count_history())
    assert not _day_is_monthly_record(date(2020, 9, 4), _get_small_count_history())
    assert not _day_is_monthly_record(date(2020, 9, 5), _get_small_count_history())
    assert not _day_is_monthly_record(date(2020, 9, 3), _get_rivoli_test_count_history())
    assert not _day_is_monthly_record(date(2020, 9, 4), _get_rivoli_test_count_history())


def test_day_rank():
    assert _day_rank(date.today(), CountHistory([DayCount(date.today(), 10)])) == 0
    assert _day_rank(date(2020, 8, 31), _get_small_count_history()) == 4
    assert _day_rank(date(2020, 9, 1), _get_small_count_history()) == 2
    assert _day_rank(date(2020, 9, 2), _get_small_count_history()) == 0
    assert _day_rank(date(2020, 9, 3), _get_small_count_history()) == 1
    assert _day_rank(date(2020, 9, 4), _get_small_count_history()) == 5
    assert _day_rank(date(2020, 9, 5), _get_small_count_history()) == 3
    assert _day_rank(date(2020, 9, 3), _get_rivoli_test_count_history()) == 8


def test_optimistic_rank():
    assert _optimistic_rank(1, [1, 1, 1]) == 0
    assert _optimistic_rank(1, [1] * 10) == 0
    assert _optimistic_rank(1, [2] * 10 + [1]) == 10
    assert _optimistic_rank(1, [2] * 10 + [1] * 30) == 10
    assert _optimistic_rank(2, [3, 1, 2]) == 1
    assert _optimistic_rank(2, [3, 1, 2, 10, 34, 12]) == 4
    assert _optimistic_rank(1, [3, 1, 2, 10, 34, 12]) == 5
    assert _optimistic_rank(1, [3, 1, 2, 10, 34, 12, 1]) == 5


def test_day_is_last_day_of_month():
    assert _day_is_last_day_of_month(date(2020, 1, 31))
    assert _day_is_last_day_of_month(date(2020, 3, 31))
    assert _day_is_last_day_of_month(date(1928, 12, 31))
    assert _day_is_last_day_of_month(date(2032, 3, 31))
    assert _day_is_last_day_of_month(date(2020, 2, 29))
    assert _day_is_last_day_of_month(date(2020, 12, 31))
    assert not _day_is_last_day_of_month(date(2020, 2, 28))
    assert not _day_is_last_day_of_month(date(2020, 1, 1))
    assert not _day_is_last_day_of_month(date(2020, 3, 1))
    assert not _day_is_last_day_of_month(date(1928, 12, 1))
    assert not _day_is_last_day_of_month(date(2032, 3, 4))
    assert not _day_is_last_day_of_month(date(2020, 1, 1))
    assert not _day_is_last_day_of_month(date(2020, 12, 1))


def test_day_is_first_day_of_year():
    assert _day_is_first_day_of_year(date(2020, 1, 1))
    assert not _day_is_first_day_of_year(date(2020, 3, 1))
    assert not _day_is_first_day_of_year(date(1928, 12, 1))
    assert not _day_is_first_day_of_year(date(2032, 3, 4))
    assert _day_is_first_day_of_year(date(2020, 1, 1))
    assert not _day_is_first_day_of_year(date(2020, 12, 1))


def test_day_is_first_day_of_month():
    assert _day_is_first_day_of_month(date(2020, 1, 1))
    assert _day_is_first_day_of_month(date(2020, 3, 1))
    assert _day_is_first_day_of_month(date(1928, 12, 1))
    assert not _day_is_first_day_of_month(date(2032, 3, 4))
    assert not _day_is_first_day_of_month(date(2020, 1, 18))
    assert not _day_is_first_day_of_month(date(2020, 12, 2))


def test_extract_total_count():
    assert _extract_total_count(CountHistory([])) == 0
    assert _extract_total_count(_get_small_count_history()) == 1070
    assert _extract_total_count(_get_rivoli_test_count_history()) == 2841547


def test_get_month():
    assert _get_month(date.today()) == Month(date.today().month, date.today().year)
    assert _get_month(parse_ymd('2020/08/09')) == Month(8, 2020)
    assert _get_month(parse_ymd('2000/07/09')) == Month(7, 2000)


def test_group_by_month():
    assert _group_by_month(CountHistory([])) == {}
    grouped = _group_by_month(_get_small_count_history())
    assert grouped[Month(8, 2020)] == [100]
    assert grouped[Month(9, 2020)] == [200, 350, 250, 50, 120]


def test_group_by_year():
    assert _group_by_year(CountHistory([])) == {}
    assert _group_by_year(_get_small_count_history()) == {2020: [100, 200, 350, 250, 50, 120]}


def test_cumulate():
    assert _cumulate([1] * 10) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert _cumulate([1] * 3) == [1, 2, 3]
    assert _cumulate([1, 2, 3]) == [1, 3, 6]
    assert _cumulate([]) == []


def test_month_to_cumulate_sums():
    assert _month_to_cumulate_sums(CountHistory([])) == {}
    cumsums = _month_to_cumulate_sums(_get_small_count_history())
    assert len(cumsums) == 2
    assert cumsums[Month(8, 2020)] == [100]
    assert cumsums[Month(9, 2020)] == [200, 550, 800, 850, 970]


def test_get_month_range():
    assert _get_month_range(Month(5, 1993)) == 31
    assert _get_month_range(Month(3, 2020)) == 31
    assert _get_month_range(Month(2, 2020)) == 29
    assert _get_month_range(Month(2, 2021)) == 28
    assert _get_month_range(Month(12, 2021)) == 31


def test_number_is_funny():
    assert _number_is_funny(1000)
    assert _number_is_funny(9999)
    assert _number_is_funny(1000000)
    assert _number_is_funny(9000)
    assert _number_is_funny(777)
    assert not _number_is_funny(31)
    assert not _number_is_funny(319)
    assert not _number_is_funny(1001)
    assert not _number_is_funny(10001)
    assert not _number_is_funny(999990)
