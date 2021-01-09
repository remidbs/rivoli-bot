from dataclasses import dataclass
from enum import Enum
from typing import Optional

from rivoli.models import Hashtag
from rivoli.params import (
    RIVOLI_BOT_SLACK,
    RIVOLI_TWITTER_ACCESS_TOKEN,
    RIVOLI_TWITTER_ACCESS_TOKEN_SECRET,
    RIVOLI_TWITTER_CUSTOMER_API_KEY,
    RIVOLI_TWITTER_CUSTOMER_API_SECRET_KEY,
    SEBASTOPOL_TWITTER_ACCESS_TOKEN,
    SEBASTOPOL_TWITTER_ACCESS_TOKEN_SECRET,
    SEBASTOPOL_TWITTER_CUSTOMER_API_KEY,
    SEBASTOPOL_TWITTER_CUSTOMER_API_SECRET_KEY,
)
from rivoli.utils import check_str


@dataclass
class TwitterSettings:
    twitter_customer_api_key: str
    twitter_customer_api_secret_key: str
    twitter_access_token: str
    twitter_access_token_secret: str

    def __post_init__(self) -> None:
        check_str(self.twitter_customer_api_key)
        check_str(self.twitter_customer_api_secret_key)
        check_str(self.twitter_access_token)
        check_str(self.twitter_access_token_secret)


@dataclass
class SlackSettings:
    url: str

    def __post_init__(self) -> None:
        check_str(self.url)


@dataclass
class Settings:
    twitter: Optional[TwitterSettings]
    slack: Optional[SlackSettings]
    hashtag: Optional[Hashtag]
    counter_id: str


class CounterName(Enum):
    RIVOLI = 'RIVOLI'
    SEBASTOPOL = 'SEBASTOPOL'


def get_settings(counter: CounterName) -> Settings:
    if counter == CounterName.RIVOLI:
        return Settings(
            TwitterSettings(
                RIVOLI_TWITTER_CUSTOMER_API_KEY,
                RIVOLI_TWITTER_CUSTOMER_API_SECRET_KEY,
                RIVOLI_TWITTER_ACCESS_TOKEN,
                RIVOLI_TWITTER_ACCESS_TOKEN_SECRET,
            ),
            SlackSettings(RIVOLI_BOT_SLACK),
            Hashtag('#CompteurRivoli'),
            '100154889',
        )
    if counter == CounterName.SEBASTOPOL:
        return Settings(
            TwitterSettings(
                SEBASTOPOL_TWITTER_CUSTOMER_API_KEY,
                SEBASTOPOL_TWITTER_CUSTOMER_API_SECRET_KEY,
                SEBASTOPOL_TWITTER_ACCESS_TOKEN,
                SEBASTOPOL_TWITTER_ACCESS_TOKEN_SECRET,
            ),
            SlackSettings(RIVOLI_BOT_SLACK),
            Hashtag('#CompteurSebastopol'),
            '100158705',
        )
    raise NotImplementedError(f'Counter {counter} has no settings.')
