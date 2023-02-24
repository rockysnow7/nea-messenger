from enum import Enum
from dataclasses import dataclass


class UIDataTopic(Enum):
    CREATE_USER         = 0
    LOG_IN              = 1
    SETTINGS            = 2
    GET_USER_CHAT_NAMES = 3
    GET_ALL_USERNAMES   = 4
    GET_IP_ADDR         = 5
    VERNAM_KEY          = 6

@dataclass
class UIData:
    topic: UIDataTopic
    success: bool
    value: any = None
