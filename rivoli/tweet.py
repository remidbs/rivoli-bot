import argparse
import random
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional, Union

from tweepy.models import Status

from rivoli.compute import build_tweet
from rivoli.config import CounterName, SlackSettings, TwitterSettings, get_settings
from rivoli.models import CountHistory, Hashtag, Tweet
from rivoli.twitter import get_tweepy_api
from rivoli.utils import get_enum_choices, load_file, parse_dmy, post_to_slack


class Output(Enum):
    STD = 'STD'
    TWITTER = 'TWITTER'
    SLACK = 'SLACK'


def _ensure_dict(obj: Any) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ValueError(f'Expecting type dict, received {type(obj)}')
    return obj


def _load_count_history(input_filename: str) -> CountHistory:
    return CountHistory.from_csv(load_file(input_filename))


def _raise_if_error(response: Any) -> None:
    if not isinstance(response, Status):
        raise ValueError(f'Unexpected response type {type(response)}. str(response) = {str(response)}')


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


@dataclass
class SlackHandler:
    settings: SlackSettings

    def handle_tweet(self, tweet: Tweet) -> None:
        post_to_slack(self.settings.url, tweet.content)


Handler = Union[TwitterHandler, SlackHandler, StdOutHandler]


def _get_day(count_history: CountHistory, target_day_desc: Union[date, str]) -> date:
    if target_day_desc == 'last':
        return max(count_history.day_to_count.keys())
    if target_day_desc == 'random':
        return random.choice(list(count_history.day_to_count.keys()))
    if isinstance(target_day_desc, str):
        raise ValueError(f'Expecting value "last", "random" or date value. Received {target_day_desc}')
    return target_day_desc


def load_data_and_dispatch_tweet(
    input_filename: str, handler: Handler, target_day_desc: Union[date, str], hashtag: Optional[Hashtag]
) -> None:
    count_history = _load_count_history(input_filename)
    target_day = _get_day(count_history, target_day_desc)
    tweet = build_tweet(target_day, count_history, date.today(), hashtag)
    handler.handle_tweet(tweet)


def _build_target_day(arg: str) -> Union[date, str]:
    if arg == 'last':
        return 'last'
    if arg == 'random':
        return 'random'
    return parse_dmy(arg)


def _get_hashtag(counter_name: Optional[str]) -> Optional[Hashtag]:
    if not counter_name:
        return None
    counter = CounterName(counter_name)
    return get_settings(counter).hashtag


def _build_handler(args: argparse.Namespace) -> Handler:
    output = Output(args.output)
    counter = CounterName(args.counter) if args.counter else None
    if output == Output.STD:
        return StdOutHandler()
    if output == Output.SLACK:
        if counter:
            settings = get_settings(counter)
            if settings.slack:
                return SlackHandler(settings.slack)
        return SlackHandler(SlackSettings(args.slack_url))
    if output == Output.TWITTER:
        if counter:
            settings = get_settings(counter)
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
    parser.add_argument('--output', '-o', type=str, choices=get_enum_choices(Output), required=True)
    parser.add_argument(
        '--target-day', '-d', type=str, default='last', help='last, random or date in format DD/MM/YYYY'
    )
    parser.add_argument('--input-filename', '-i', type=str, required=True)
    parser.add_argument('--counter', type=str, choices=get_enum_choices(CounterName), required=False)
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
    hashtag = _get_hashtag(args.counter)
    load_data_and_dispatch_tweet(args.input_filename, handler, target_day, hashtag)


if __name__ == '__main__':
    cli()
