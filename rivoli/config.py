import tweepy

from rivoli.secrets import secrets
from typing import Optional

ECO_COUNTER_URL = secrets['ecoCounterUrl']
ZAPIER_WEBHOOK_URL = secrets['zapierWebhookUrl']
SLACK_TEST_URL = secrets['slackTestUrl']
TWITTER_CUSTOMER_API_KEY = secrets['twitterCustomerAPIKey']
TWITTER_CUSTOMER_API_SECRET_KEY = secrets['twitterCustomerAPISecretKey']
TWITTER_ACCESS_TOKEN = secrets['twitterAccessToken']
TWITTER_ACCESS_TOKEN_SECRET = secrets['twitterAccessTokenSecret']


twitter_api: Optional[tweepy.API] = None


def get_twitter() -> tweepy.API:
    global twitter_api
    if not twitter_api:
        auth = tweepy.OAuthHandler(TWITTER_CUSTOMER_API_KEY, TWITTER_CUSTOMER_API_SECRET_KEY)
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
        twitter_api = tweepy.API(auth)
    return twitter_api
