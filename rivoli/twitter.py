import tweepy

from rivoli.config import TwitterSettings


def get_tweepy_api(settings: TwitterSettings) -> tweepy.API:
    auth = tweepy.OAuthHandler(settings.twitter_customer_api_key, settings.twitter_customer_api_secret_key)
    auth.set_access_token(settings.twitter_access_token, settings.twitter_access_token_secret)
    twitter_api = tweepy.API(auth)
    return twitter_api
