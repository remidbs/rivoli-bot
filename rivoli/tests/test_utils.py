from datetime import date
from rivoli.utils import date_to_french_month


def test_date_to_french_month():
    assert date_to_french_month(date(2020, 1, 1)) == 'Janvier 2020'
    assert date_to_french_month(date(2020, 2, 1)) == 'Février 2020'
    assert date_to_french_month(date(2020, 2, 10)) == 'Février 2020'
