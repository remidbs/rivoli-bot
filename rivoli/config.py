from dataclasses import dataclass
from enum import Enum

from rivoli.secrets import (
    RIVOLI_TWITTER_ACCESS_TOKEN,
    RIVOLI_TWITTER_ACCESS_TOKEN_SECRET,
    RIVOLI_TWITTER_CUSTOMER_API_KEY,
    RIVOLI_TWITTER_CUSTOMER_API_SECRET_KEY,
    SEBASTOPOL_TWITTER_ACCESS_TOKEN,
    SEBASTOPOL_TWITTER_ACCESS_TOKEN_SECRET,
    SEBASTOPOL_TWITTER_CUSTOMER_API_KEY,
    SEBASTOPOL_TWITTER_CUSTOMER_API_SECRET_KEY,
)


@dataclass
class TwitterSettings:
    twitter_customer_api_key: str
    twitter_customer_api_secret_key: str
    twitter_access_token: str
    twitter_access_token_secret: str


@dataclass
class Settings:
    twitter: TwitterSettings
    counter_id: str


class CounterName(Enum):
    RIVOLI = 'RIVOLI'
    SEBASTOPOL = 'SEBASTOPOL'


_ECO_COUNTER_ID = {
    CounterName.RIVOLI: '100154889',
    CounterName.SEBASTOPOL: '100158705',
}


def get_settings(counter: CounterName) -> Settings:
    if counter == CounterName.RIVOLI:
        return Settings(
            TwitterSettings(
                RIVOLI_TWITTER_CUSTOMER_API_KEY,
                RIVOLI_TWITTER_CUSTOMER_API_SECRET_KEY,
                RIVOLI_TWITTER_ACCESS_TOKEN,
                RIVOLI_TWITTER_ACCESS_TOKEN_SECRET,
            ),
            _ECO_COUNTER_ID[counter],
        )
    if counter == CounterName.SEBASTOPOL:
        return Settings(
            TwitterSettings(
                SEBASTOPOL_TWITTER_CUSTOMER_API_KEY,
                SEBASTOPOL_TWITTER_CUSTOMER_API_SECRET_KEY,
                SEBASTOPOL_TWITTER_ACCESS_TOKEN,
                SEBASTOPOL_TWITTER_ACCESS_TOKEN_SECRET,
            ),
            _ECO_COUNTER_ID[counter],
        )
    raise NotImplementedError(f'Counter {counter} has no settings.')
