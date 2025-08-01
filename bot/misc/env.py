import os
from abc import ABC
from typing import Final


class EnvKeys(ABC):
    TOKEN: Final = '8361461005:AAH5HPuOxtwiTQjhrCUPMNqImdYU3xnTLfs'
    OWNER_ID: Final = '7685655006'
    ACCESS_TOKEN: Final = os.environ.get('ACCESS_TOKEN')
    ACCOUNT_NUMBER: Final = os.environ.get('ACCOUNT_NUMBER')
