import random
import traceback
from typing import Any, Callable, List

from rivoli.config import CounterName
from rivoli.main import fetch_data_and_post_tweet_to_slack, fetch_data_and_publish_tweet
from rivoli.params import RIVOLI_BOT_SLACK
from rivoli.utils import post_to_slack


def execute_and_publish_output(func: Callable, args: List[Any]):
    args_str = ", ".join(map(str, args))
    func_name = func.__name__
    try:
        func(*args)
        success_message = f'Succesfully executed {func_name}({args_str})'
        post_to_slack(RIVOLI_BOT_SLACK, success_message)
    except Exception:  # pylint: disable=broad-except
        message = '\n'.join([f'Failed executing function {func_name}({args_str})', traceback.format_exc()])
        post_to_slack(RIVOLI_BOT_SLACK, message)


def rivoli_post_to_slack():
    random.seed(1)
    execute_and_publish_output(fetch_data_and_post_tweet_to_slack, [CounterName.RIVOLI])


def sebastopol_post_to_slack():
    random.seed(2)
    execute_and_publish_output(fetch_data_and_post_tweet_to_slack, [CounterName.SEBASTOPOL])


def rivoli_tweet():
    random.seed(1)
    execute_and_publish_output(fetch_data_and_publish_tweet, [CounterName.RIVOLI])


def sebastopol_tweet():
    random.seed(2)
    execute_and_publish_output(fetch_data_and_publish_tweet, [CounterName.SEBASTOPOL])
