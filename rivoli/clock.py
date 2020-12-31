import random
import string
import traceback
from datetime import date, timedelta
from typing import Any, Callable, List

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

from rivoli.config import CounterName, get_settings
from rivoli.fetch_data import fetch_and_dump_data
from rivoli.main import SlackHandler, main, post_to_slack
from rivoli.params import RIVOLI_BOT_SLACK

SCHED = BlockingScheduler()


def _random_str() -> str:
    return ''.join([random.choice(string.ascii_letters) for _ in range(6)])


def _fetch_and_post_to_slack(counter_name: CounterName) -> None:
    filename = '/tmp/counter_data' + _random_str() + '.csv'
    fetch_and_dump_data(counter_name, filename)
    settings = get_settings(CounterName.RIVOLI)
    if not settings.slack:
        raise ValueError('Expecting slack url to be defined.')
    handler = SlackHandler(settings.slack)
    main(filename, handler, date.today() - timedelta(days=1))


def _post_exceptions_to_slack(func: Callable, args: List[Any]):
    try:
        func(*args)
    except Exception:  # pylint: disable=broad-except
        message = '\n'.join([f'Failed executing function {func} with args {args}', traceback.format_exc()])
        post_to_slack(RIVOLI_BOT_SLACK, message)


@SCHED.scheduled_job('cron', hour=7, minute=0, timezone=pytz.timezone('Europe/Paris'))
def rivoli_post_to_slack():
    _post_exceptions_to_slack(_fetch_and_post_to_slack, [CounterName.RIVOLI])


@SCHED.scheduled_job('cron', hour=7, minute=0, timezone=pytz.timezone('Europe/Paris'))
def sebastopol_post_to_slack():
    _post_exceptions_to_slack(_fetch_and_post_to_slack, [CounterName.SEBASTOPOL])


# @SCHED.scheduled_job('cron', hour=9, timezone=pytz.timezone('Europe/Paris'))
# def rivoli_tweet():
#     print('This job is run every weekday at 5pm.')


SCHED.start()
