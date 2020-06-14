from typing import Optional


import tweepy

from rivoli.secrets import SECRETS

ECO_COUNTER_URL = SECRETS['ecoCounterUrl']
ECO_COUNTER_GLOBAL_URL = SECRETS['ecoCounterGlobal']
ZAPIER_WEBHOOK_URL = SECRETS['zapierWebhookUrl']
SLACK_TEST_URL = SECRETS['slackTestUrl']
TWITTER_CUSTOMER_API_KEY = SECRETS['twitterCustomerAPIKey']
TWITTER_CUSTOMER_API_SECRET_KEY = SECRETS['twitterCustomerAPISecretKey']
TWITTER_ACCESS_TOKEN = SECRETS['twitterAccessToken']
TWITTER_ACCESS_TOKEN_SECRET = SECRETS['twitterAccessTokenSecret']


twitter_api: Optional[tweepy.API] = None


def get_twitter() -> tweepy.API:
    global twitter_api
    if not twitter_api:
        auth = tweepy.OAuthHandler(TWITTER_CUSTOMER_API_KEY, TWITTER_CUSTOMER_API_SECRET_KEY)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
        twitter_api = tweepy.API(auth)
    return twitter_api
