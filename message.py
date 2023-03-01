import json
import time
import base64
import constants

from enum import Enum
from copy import deepcopy
from encoding import zfill_bytes, zremove_bytes


class Data:
    def __init__(self, value: any = b""):
        self.value = value

    def __repr__(self) -> str:
        return f"Data({self.value})"

    def __iter__(self):
        yield from self.value

    def __int__(self) -> int:
        return 0

    def as_JSON_str(self) -> str:
        value = self.value
        if isinstance(self.value, bytes):
            value = "".join(chr(c) for c in self.value)

        self_dict = {
            "type": int(self),
            "value": value,
        }
        self_dict_json = json.dumps(self_dict)

        return self_dict_json

class TextData(Data):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self) -> str:
        return f"TextData(\"{self.value}\")"

    def __int__(self) -> int:
        return 1

class CommandData(Data):
    def __init__(self, value: str):
        self.value = value

    def __repr__(self) -> str:
        return f"CommandData(\"{self.value}\")"

    def __int__(self) -> int:
        return 2

def Data_from_JSON_str(s: str) -> Data:
    data_json = json.loads(s)

    if data_json["type"] == 0:
        return Data(data_json["value"])

    if data_json["type"] == 1:
        return TextData(data_json["value"])

    if data_json["type"] == 2:
        return CommandData(data_json["value"])

    raise ValueError(f"Data cannot have type {data_json['type']} from JSON.")


class MessagePurpose(Enum):
    MESSAGE                     = 0
    KEY                         = 1
    EXCHANGE                    = 2
    CREATE_USER                 = 3
    CREATE_USER_USERNAME_TAKEN  = 4
    CREATE_USER_DONE            = 5
    CREATE_CHAT                 = 6
    TEST_LOGIN                  = 7
    TEST_LOGIN_SUCCESS          = 8
    TEST_LOGIN_FAILURE          = 9
    GET_USER_CHAT_NAMES         = 10
    SET_COLOR                   = 11
    GET_SETTINGS                = 12
    GET_ALL_USERNAMES           = 13
    GET_IP_ADDR                 = 14
    GET_CHAT_DATA               = 15
    GET_CHAT_MESSAGES           = 16

class Message:
    def __init__(
        self,
        mes_purpose: MessagePurpose,
        sender: str,
        content: Data,
        *,
        sender_username: str = "",
        chat_name: str = "",
        is_encrypted: bool = False,
        timestamp: float = time.time(),
    ):
        self.is_encrypted = is_encrypted
        self.sender = sender
        self.sender_username = sender_username
        self.chat_name = chat_name
        self.mes_purpose = mes_purpose
        self.content = content
        self.timestamp = timestamp

    def __repr__(self) -> str:
        return f"Message({self.is_encrypted}, {self.mes_purpose}, {self.sender}, {self.sender_username}, {self.chat_name}, {self.content}, {self.timestamp})"

    def __as_JSON_str(self) -> str:
        self_dict = deepcopy(self.__dict__)
        self_dict["mes_purpose"] = self.mes_purpose.value
        self_dict["content"] = self.content.as_JSON_str()
        self_dict["timestamp"] = self.timestamp
        self_dict_json = json.dumps(self_dict)

        return self_dict_json

    def __bytes__(self) -> bytes:
        return self.__as_JSON_str().encode("utf-8")

    @staticmethod
    def dict_from_bytes(b: bytes) -> dict:
        self_dict = json.loads(b)
        self_dict["mes_purpose"] = MessagePurpose(self_dict["mes_purpose"])
        self_dict["content"] = Data_from_JSON_str(self_dict["content"])

        return self_dict

    @staticmethod
    def from_dict(d: dict) -> "Message":
        return Message(
            d["mes_purpose"],
            d["sender"],
            d["content"],
            chat_name=d["chat_name"],
            is_encrypted=d["is_encrypted"],
            timestamp=d["timestamp"],
        )

    @staticmethod
    def from_bytes(b: bytes) -> "Message":
        return Message.from_dict(Message.dict_from_bytes(b))
