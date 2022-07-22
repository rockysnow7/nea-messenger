from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
	TEXT = 0

@dataclass
class Message:
	message_type: MessageType
	content: str
	sender_username: str
	chat_name: str
