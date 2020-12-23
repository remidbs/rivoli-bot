import argparse
from enum import Enum
from typing import Any, List, Tuple

import requests

from rivoli.config import ECO_COUNTER_URL_TEMPLATE
from rivoli.exceptions import FailedRequestingEcoCounterError
from rivoli.models import CountHistory, DayCount
from rivoli.utils import parse_mdy, write_json


class Counter(Enum):
    RIVOLI = 'RIVOLI'
    SEBASTOPOL = 'SEBASTOPOL'


_ECO_COUNTER_ID = {
    Counter.RIVOLI: '100154889',
    Counter.SEBASTOPOL: '100158705',
}


def test_missing_counter_ids():
    for counter in list(Counter):
        assert counter in _ECO_COUNTER_ID


def _build_url(counter_name: Counter) -> str:
    counter_id = _ECO_COUNTER_ID[counter_name]
    return ECO_COUNTER_URL_TEMPLATE.format(counter_id, counter_id)


def _build_count_history(pairs: List[Tuple[str, str]]) -> CountHistory:
    daily_counts: List[DayCount] = []
    for date_str, count_str in pairs:
        date_ = parse_mdy(date_str)
        count = int(float(count_str))
        daily_counts.append(DayCount(date_, count))
    return CountHistory(daily_counts)


def _check_response_content(response_content: Any) -> List[Tuple[str, str]]:
    if not isinstance(response_content, list):
        raise ValueError(f'Expecting list, received {type(response_content)}')
    formatted_result: List[Tuple[str, str]] = []
    for pair in response_content:
        if not isinstance(pair, list):
            raise ValueError(f'Expecting list, received {type(pair)}')
        if len(pair) != 2:
            raise ValueError(f'Expecting list of length 2, received list of length {len(pair)}')
        if not isinstance(pair[0], str):
            raise ValueError(f'Expecting str, received {type(pair[0])}')
        if not isinstance(pair[1], str):
            raise ValueError(f'Expecting str, received {type(pair[1])}')
        formatted_result.append((pair[0], pair[1]))
    return formatted_result


def _fetch_data_from_ecocounter(counter_name: Counter) -> CountHistory:
    url = _build_url(counter_name)
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        raise FailedRequestingEcoCounterError(response.content.decode())
    return _build_count_history(_check_response_content(response.json()))


def fetch_and_dump_data(counter_name: Counter, filename: str) -> None:
    count_history = _fetch_data_from_ecocounter(counter_name)
    write_json(count_history.to_json(), filename)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename', type=str)
    parser.add_argument('counter', type=str, choices=list(map(lambda x: x.value, list(Counter))))
    args = parser.parse_args()
    fetch_and_dump_data(Counter(args.counter), args.filename)


if __name__ == '__main__':
    cli()
