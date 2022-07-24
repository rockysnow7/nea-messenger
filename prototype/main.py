import sqlite3
import ip
import encoding

from server import Server
from message import Message, MessageType


server = Server()

server.create_new_chat(
    "test_chat",
    1234,
    ["finn", "other"],
    ["finn"],
)
