import constants

from enum import Enum
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

    def __bytes__(self) -> bytes:
        value = self.value.encode("utf-8") if isinstance(self.value, str) else self.value
        value = zfill_bytes(value, constants.MESSAGE_CONTENT_MAX_LEN)

        return bytes([int(self)]) + value

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
        return f"TextData(\"{self.value}\")"

    def __int__(self) -> int:
        return 2

def Data_from_bytes(s: bytes) -> Data:
    if s[0] == 0:
        return Data(s)

    if s[0] == 1:
        return TextData(s.decode("utf-8"))

    return CommandData(s.decode("utf-8"))


class MessagePurpose(Enum): # user_bit * 1, count_bit * 4
    KEY         = 0b00000
    EXCHANGE    = 0b00001
    CREATE_USER = 0b00010
    MESSAGE     = 0b10000

class Message:
    def __init__(
        self,
        mes_purpose: MessagePurpose,
        sender: str,
        content: Data,
        *,
        chat_name: str = "",
        metadata: Data = Data(),
        is_encrypted: bool = False,
    ):
        self.is_encrypted = is_encrypted
        self.sender = sender
        self.chat_name = chat_name
        self.mes_purpose = mes_purpose
        self.content = content
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"Message({self.is_encrypted}, {self.mes_purpose}, {self.sender}, {self.chat_name}, {self.content}, {self.metadata})"

    def __bytes__(self) -> bytes:
        """
        Returns a bytes representation of the message, of the following form:
            is_encrypted (1)
            sender       (USERNAME_MAX_LEN)
            chat_name    (CHAT_NAME_MAX_LEN)
            mes_purpose  (1)
            content      (MESSAGE_CONTENT_MAX_LEN)
            metadata     (MESSAGE_CONTENT_MAX_LEN)
        """

        b = b""

        is_encrypted = bytes([self.is_encrypted])
        #input(f"{is_encrypted=}")
        b += is_encrypted

        sender = zfill_bytes(self.sender.encode("utf-8"), constants.USERNAME_MAX_LEN)
        #input(f"{sender=}")
        b += sender

        chat_name = zfill_bytes(self.chat_name.encode("utf-8"), constants.CHAT_NAME_MAX_LEN)
        #input(f"{chat_name=}")
        b += chat_name

        mes_purpose = bytes([self.mes_purpose.value])
        #input(f"{mes_purpose=}")
        b += mes_purpose

        content = bytes(self.content)
        #input(f"{content=}")
        b += content

        metadata = bytes(self.metadata)
        #input(f"{metadata=}")
        b += metadata

        return b

    @staticmethod
    def from_bytes(b: bytes) -> "Message":
        is_encrypted = b[0] == b"\1"
        b = b[1:]
        sender = zremove_bytes(b[:constants.USERNAME_MAX_LEN]).decode("utf-8")
        b = b[constants.USERNAME_MAX_LEN:]
        chat_name = zremove_bytes(b[:constants.CHAT_NAME_MAX_LEN]).decode("utf-8")
        b = b[constants.CHAT_NAME_MAX_LEN:]
        mes_purpose = MessagePurpose(int(b[0]))
        b = b[1:]
        content = Data_from_bytes(b[:1 + constants.MESSAGE_CONTENT_MAX_LEN])
        b = b[1 + constants.MESSAGE_CONTENT_MAX_LEN:]
        metadata = Data_from_bytes(b[:1 + constants.MESSAGE_CONTENT_MAX_LEN])

        return Message(
            mes_purpose,
            sender,
            content,
            chat_name=chat_name,
            metadata=metadata,
            is_encrypted=is_encrypted,
        )
