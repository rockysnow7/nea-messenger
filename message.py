from enum import Enum


class Data:
    def __init__(self, value: any = []):
        self.value = value

    def __repr__(self) -> str:
        return f"Data({self.value})"

    def __iter__(self):
        yield from self.value

    def __int__(self) -> int:
        return 0

class TextData(Data):
    def __init__(self, value: str | list[int]):
        if isinstance(value, str):
            self.value = [ord(c) for c in value]
        else:
            self.value = value

    def __repr__(self) -> str:
        value = "".join(chr(i) for i in self.value)

        return f"TextData(\"{value}\")"

    def __int__(self) -> int:
        return 1

class CommandData(Data):
    def __init__(self, value: str):
        if isinstance(value, str):
            self.value = [ord(c) for c in value]

    def __repr__(self) -> str:
        value = "".join(chr(i) for i in self.value)

        return f"TextData({value})"

    def __int__(self) -> int:
        return 2


class MessagePurpose(Enum): # user_bit * 1, count_bit * 4
    KEY      = 0b00000
    EXCHANGE = 0b00001
    COMMAND  = 0b00010
    MESSAGE  = 0b10000

class Message:
    def __init__(
        self,
        mes_purpose: MessagePurpose,
        sender: str,
        chat_name: str,
        content: Data,
        *,
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
