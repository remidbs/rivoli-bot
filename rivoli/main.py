import argparse
import os
import random
import string
from datetime import date, timedelta

from rivoli.config import CounterName, get_settings
from rivoli.fetch_data import fetch_and_dump_data
from rivoli.tweet import Handler, SlackHandler, StdOutHandler, load_data_and_dispatch_tweet
from rivoli.utils import get_enum_choices


def _random_str() -> str:
    return ''.join([random.choice(string.ascii_letters) for _ in range(6)])


def _fetch_data_and_post_tweet(counter_name: CounterName, handler: Handler) -> None:
    filename = '/tmp/counter_data' + _random_str() + '.csv'
    fetch_and_dump_data(counter_name, filename)
    settings = get_settings(counter_name)
    load_data_and_dispatch_tweet(filename, handler, date.today() - timedelta(days=1), settings.hashtag)
    os.remove(filename)


def fetch_data_and_post_tweet_to_slack(counter_name: CounterName) -> None:
    settings = get_settings(counter_name)
    if not settings.slack:
        raise ValueError('Expecting slack url to be defined.')
    handler = SlackHandler(settings.slack)
    _fetch_data_and_post_tweet(counter_name, handler)


def fetch_data_and_print_tweet(counter_name: CounterName) -> None:
    _fetch_data_and_post_tweet(counter_name, StdOutHandler())


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--counter', '-c', type=str, choices=get_enum_choices(CounterName), required=True)
    parser.add_argument('--slack', '-s', type=bool, default=False, const=True, nargs='?')
    args = parser.parse_args()
    counter_name = CounterName(args.counter)
    if args.slack:
        fetch_data_and_post_tweet_to_slack(counter_name)
    else:
        fetch_data_and_print_tweet(counter_name)


if __name__ == '__main__':
    cli()
