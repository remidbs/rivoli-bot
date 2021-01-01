import traceback
from typing import Any, Callable, List

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

from rivoli.config import CounterName
from rivoli.main import fetch_data_and_post_tweet_to_slack
from rivoli.params import RIVOLI_BOT_SLACK
from rivoli.utils import post_to_slack

SCHED = BlockingScheduler()


def _post_exceptions_to_slack(func: Callable, args: List[Any]):
    try:
        func(*args)
    except Exception:  # pylint: disable=broad-except
        message = '\n'.join([f'Failed executing function {func} with args {args}', traceback.format_exc()])
        post_to_slack(RIVOLI_BOT_SLACK, message)


@SCHED.scheduled_job('cron', hour=7, minute=0, timezone=pytz.timezone('Europe/Paris'))
def rivoli_post_to_slack():
    _post_exceptions_to_slack(fetch_data_and_post_tweet_to_slack, [CounterName.RIVOLI])


@SCHED.scheduled_job('cron', hour=7, minute=0, timezone=pytz.timezone('Europe/Paris'))
def sebastopol_post_to_slack():
    _post_exceptions_to_slack(fetch_data_and_post_tweet_to_slack, [CounterName.SEBASTOPOL])


# @SCHED.scheduled_job('cron', hour=9, timezone=pytz.timezone('Europe/Paris'))
# def rivoli_tweet():
#     print('This job is run every weekday at 5pm.')


SCHED.start()
