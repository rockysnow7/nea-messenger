from enum import Enum
from dataclasses import dataclass


class UIDataTopic(Enum):
    VERNAM_KEY          = 0
    CREATE_USER         = 1
    LOG_IN              = 2
    SETTINGS            = 3
    GET_USER_CHAT_NAMES = 4
    GET_ALL_USERNAMES   = 5
    GET_IP_ADDR         = 6
    GET_CHAT_DATA       = 7
    GET_CHAT_MESSAGES   = 8

@dataclass
class UIData:
    topic: UIDataTopic
    success: bool
    value: any = None
