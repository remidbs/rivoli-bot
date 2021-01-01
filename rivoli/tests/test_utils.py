from datetime import date
from rivoli.utils import date_to_french_month, get_enum_choices
from enum import Enum


def test_date_to_french_month():
    assert date_to_french_month(date(2020, 1, 1)) == 'Janvier 2020'
    assert date_to_french_month(date(2020, 2, 1)) == 'Février 2020'
    assert date_to_french_month(date(2020, 2, 10)) == 'Février 2020'


class _EnumExample(Enum):
    A = 'A'
    B = 'B'
    C = 'C'


def test_get_enum_choices():
    assert set(get_enum_choices(_EnumExample)) == {'A', 'B', 'C'}
