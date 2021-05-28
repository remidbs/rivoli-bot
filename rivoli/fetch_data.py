import argparse
from typing import Any, List, Tuple

import requests

from rivoli.config import CounterName
from rivoli.exceptions import FailedRequestingEcoCounterError
from rivoli.models import CountHistory, DayCount
from rivoli.params import RIVOLI_URL, SEBASTOPOL_URL
from rivoli.utils import parse_mdy, write_json, write_str


def _build_url(counter_name: CounterName) -> str:
    if counter_name == counter_name.SEBASTOPOL:
        return SEBASTOPOL_URL
    if counter_name == counter_name.RIVOLI:
        return RIVOLI_URL
    raise NotImplementedError(f'URL for counter {counter_name} is missing.')


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


def _fetch_data_from_ecocounter(counter_name: CounterName) -> CountHistory:
    url = _build_url(counter_name)
    response = requests.get(url, verify=False)
    if response.status_code != 200:
        raise FailedRequestingEcoCounterError(response.content.decode() + f'\nAttempted URL={url}')
    return _build_count_history(_check_response_content(response.json()))


def fetch_and_dump_data(counter_name: CounterName, filename: str) -> None:
    count_history = _fetch_data_from_ecocounter(counter_name)
    if '.csv' in filename:
        write_str(count_history.to_csv(), filename)
    else:
        write_json(count_history.to_json(), filename)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str)
    parser.add_argument('--counter', type=str, choices=list(map(lambda x: x.value, list(CounterName))))
    args = parser.parse_args()
    fetch_and_dump_data(CounterName(args.counter), args.filename)


if __name__ == '__main__':
    cli()
