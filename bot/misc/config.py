from abc import ABC
from typing import Final


class TgConfig(ABC):
    STATE: Final = {}
    CHANNEL_URL: Final = 'https://t.me/+7AGzv3xE44wzZjQy'
    HELPER_URL: Final = None
    GROUP_ID: Final = None
    REFERRAL_PERCENT = 5
    PAYMENT_TIME: Final = 1800
    RULES: Final = None
