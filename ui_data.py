from enum import Enum
from dataclasses import dataclass


class UIDataTopic(Enum):
    CREATE_USER         = 0
    LOG_IN              = 1
    GET_USER_CHAT_NAMES = 2
    SETTINGS            = 3

@dataclass
class UIData:
    topic: UIDataTopic
    success: bool
    value: any = None
