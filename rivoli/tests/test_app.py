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
    assert False


def test_day_is_absolute_maximum():
    assert False


def test_day_is_year_maximum():
    assert False


def test_day_is_monthly_record():
    assert False


def test_day_rank():
    assert False


def test_optimistic_rank():
    assert False


def test_day_is_last_day_of_month():
    assert False


def test_day_is_first_day_of_year():
    assert False


def test_day_is_first_day_of_month():
    assert False


def test_extract_total_count():
    assert False


def test_get_month():
    assert False


def test_group_by_month():
    assert False


def test_group_by_year():
    assert False


def test_cumulate():
    assert False


def test_month_to_cumulate_sums():
    assert False


def test_get_month_range():
    assert False


def test_number_is_funny():
    assert False
