import argparse
import json
import random
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, List, Union

import requests

from rivoli.compute import build_tweet
from rivoli.config import CounterName, SlackSettings, TwitterSettings, get_settings
from rivoli.models import CountHistory, Tweet
from rivoli.twitter import get_tweepy_api
from rivoli.utils import load_file, load_json, parse_dmy


def _get_value(element) -> str:
    return element.value


def _get_enum_choices(enum) -> List[str]:
    return list(map(_get_value, list(enum)))


class Output(Enum):
    STD = 'STD'
    TWITTER = 'TWITTER'
    SLACK = 'SLACK'


def _ensure_dict(obj: Any) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError(f'Expecting type dict, received {type(obj)}')
    return obj


def _load_count_history(input_filename: str) -> CountHistory:
    if '.csv' in input_filename:
        return CountHistory.from_csv(load_file(input_filename))
    return CountHistory.from_json(_ensure_dict(load_json(input_filename)))


def _raise_if_error(response):
    raise NotImplementedError(f'{type(response)}')


@dataclass
class TwitterHandler:
    settings: TwitterSettings

    def handle_tweet(self, tweet: Tweet) -> None:
        api = get_tweepy_api(self.settings)
        _raise_if_error(api.update_status(tweet.content))


@dataclass
class StdOutHandler:
    @staticmethod
    def handle_tweet(tweet: Tweet) -> None:
        print(tweet.content)


def post_to_slack(url: str, text: str) -> None:
    response = requests.post(url, data=json.dumps({'text': text}))
    if 200 <= response.status_code < 300:
        return
    raise ValueError(
        f'Failed posting to slack: status_code={response.status_code}, content={response.content.decode()}'
    )


@dataclass
class SlackHandler:
    settings: SlackSettings

    def handle_tweet(self, tweet: Tweet) -> None:
        post_to_slack(self.settings.url, tweet.content)


_Handler = Union[TwitterHandler, SlackHandler, StdOutHandler]


def _get_day(count_history: CountHistory, target_day_desc: Union[date, str]) -> date:
    if target_day_desc == 'last':
        return max(count_history.day_to_count.keys())
    if target_day_desc == 'random':
        return random.choice(list(count_history.day_to_count.keys()))
    if isinstance(target_day_desc, str):
        raise ValueError(f'Expecting value "last", "random" or date value. Received {target_day_desc}')
    return target_day_desc


def main(input_filename: str, handler: _Handler, target_day_desc: Union[date, str]) -> None:
    count_history = _load_count_history(input_filename)
    target_day = _get_day(count_history, target_day_desc)
    tweet = build_tweet(target_day, count_history, date.today())
    handler.handle_tweet(tweet)


def _build_target_day(arg: str) -> Union[date, str]:
    if arg == 'last':
        return 'last'
    if arg == 'random':
        return 'random'
    return parse_dmy(arg)


def _build_handler(args: argparse.Namespace) -> _Handler:
    output = Output(args.output)
    if output == Output.STD:
        return StdOutHandler()
    if output == Output.SLACK:
        if args.counter:
            settings = get_settings(args.counter)
            if settings.slack:
                return SlackHandler(settings.slack)
        return SlackHandler(SlackSettings(args.slack_url))
    if output == Output.TWITTER:
        if args.counter:
            settings = get_settings(args.counter)
            if settings.twitter:
                return TwitterHandler(settings.twitter)
        return TwitterHandler(
            TwitterSettings(
                args.twitter_customer_api_key,
                args.twitter_customer_api_secret_key,
                args.twitter_access_token,
                args.twitter_access_token_secret,
            )
        )
    raise NotImplementedError(f'Unhandled output mode {output}')


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', type=str, choices=_get_enum_choices(Output), required=True)
    parser.add_argument(
        '--target-day', '-d', type=str, default='last', help='last, random or date in format DD/MM/YYYY'
    )
    parser.add_argument('--input-filename', '-i', type=str, required=True)
    parser.add_argument('--counter', type=str, choices=_get_enum_choices(CounterName), required=False)
    group_twitter = parser.add_argument_group()
    group_twitter.add_argument('--twitter-customer-api-key', type=str, required=False)
    group_twitter.add_argument('--twitter-customer-api-secret_key', type=str, required=False)
    group_twitter.add_argument('--twitter-access-token', type=str, required=False)
    group_twitter.add_argument('--twitter-access-token-secret', type=str, required=False)
    group_slack = parser.add_argument_group()
    group_slack.add_argument('--slack-url', type=str, required=False)
    args = parser.parse_args()
    handler = _build_handler(args)
    target_day = _build_target_day(args.target_day)
    main(args.input_filename, handler, target_day)


if __name__ == '__main__':
    cli()
