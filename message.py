from enum import Enum


class Data:
    def __init__(self, value: any = []):
        self.value = value

    def __repr__(self) -> str:
        return f"Data({self.value})"

    def __iter__(self):
        yield from self.value

class TextData(Data):
    def __init__(self, value: str | list[int]):
        if isinstance(value, str):
            self.value = [ord(c) for c in value]
        else:
            self.value = value

    def __repr__(self) -> str:
        value = "".join(chr(i) for i in self.value)

        return f"TextData(\"{value}\")"

class CommandData(Data):
    def __init__(self, value: str):
        if isinstance(value, str):
            self.value = [ord(c) for c in value]

    def __repr__(self) -> str:
        value = "".join(chr(i) for i in self.value)

        return f"TextData({value})"


class MessagePurpose(Enum): # user_bit * 1, count_bit * 3
    KEY      = 0b00000
    EXCHANGE = 0b00001
    COMMAND  = 0b00010
    MESSAGE  = 0b10000

class Message:
    def __init__(
        self,
        mes_purpose: MessagePurpose,
        sender: str,
        recipient: str,
        content: Data,
        *,
        metadata: Data = Data(),
        is_encrypted: bool = False,
    ):
        self.is_encrypted = is_encrypted
        self.sender = sender
        self.recipient = recipient
        self.mes_purpose = mes_purpose
        self.content = content
        self.metadata = metadata

    def __repr__(self) -> str:
        return f"Message({self.is_encrypted}, {self.mes_purpose}, {self.sender}, {self.recipient}, {self.content}, {self.metadata})"
