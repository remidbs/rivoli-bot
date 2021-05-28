import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

from rivoli.entry_points.instances import rivoli_post_to_slack, rivoli_tweet, sebastopol_post_to_slack, sebastopol_tweet

SCHED = BlockingScheduler()


@SCHED.scheduled_job('cron', hour=7, minute=0, timezone=pytz.timezone('Europe/Paris'))
def _rivoli_post_to_slack():
    rivoli_post_to_slack()


@SCHED.scheduled_job('cron', hour=7, minute=0, timezone=pytz.timezone('Europe/Paris'))
def _sebastopol_post_to_slack():
    sebastopol_post_to_slack()


@SCHED.scheduled_job('cron', hour=9, minute=30, timezone=pytz.timezone('Europe/Paris'))
def _rivoli_tweet():
    rivoli_tweet()


@SCHED.scheduled_job('cron', hour=9, minute=30, timezone=pytz.timezone('Europe/Paris'))
def _sebastopol_tweet():
    sebastopol_tweet()


SCHED.start()
