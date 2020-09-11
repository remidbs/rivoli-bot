import os
from typing import Optional

import tweepy

from rivoli.secrets import SECRETS

COUNTER = os.environ['COUNTER']
if COUNTER == 'RIVOLI':
    ECO_COUNTER_URL = SECRETS['ecoCounterUrl']
    TWITTER_CUSTOMER_API_KEY = SECRETS['twitterCustomerAPIKey']
    TWITTER_CUSTOMER_API_SECRET_KEY = SECRETS['twitterCustomerAPISecretKey']
    TWITTER_ACCESS_TOKEN = SECRETS['twitterAccessToken']
    TWITTER_ACCESS_TOKEN_SECRET = SECRETS['twitterAccessTokenSecret']
elif COUNTER == 'SEBASTOPOL':
    ECO_COUNTER_URL = SECRETS['sebastopolUrl']
    TWITTER_CUSTOMER_API_KEY = SECRETS['sebastopolTwitterCustomerAPIKey']
    TWITTER_CUSTOMER_API_SECRET_KEY = SECRETS['sebastopolTwitterCustomerAPISecretKey']
    TWITTER_ACCESS_TOKEN = SECRETS['sebastopolTwitterAccessToken']
    TWITTER_ACCESS_TOKEN_SECRET = SECRETS['sebastopolTwitterAccessTokenSecret']
else:
    raise ValueError(f'Unknown counter {COUNTER}')


ECO_COUNTER_GLOBAL_URL = SECRETS['ecoCounterGlobal']
ZAPIER_WEBHOOK_URL = SECRETS['zapierWebhookUrl']
SLACK_TEST_URL = SECRETS['slackTestUrl']

twitter_api: Optional[tweepy.API] = None


def get_twitter() -> tweepy.API:
    global twitter_api
    if not twitter_api:
        auth = tweepy.OAuthHandler(TWITTER_CUSTOMER_API_KEY, TWITTER_CUSTOMER_API_SECRET_KEY)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
        twitter_api = tweepy.API(auth)
    return twitter_api
