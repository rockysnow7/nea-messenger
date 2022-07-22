import sqlite3

from server import Server
from message import Message, MessageType


server = Server()

server.create_new_chat("test", 1234, ["finn", "other"], ["finn"])
server.save_message(Message(MessageType.TEXT, "a", "finn", "test"))
server.save_message(Message(MessageType.TEXT, "b", "finn", "test"))
server.debug_display_chat_history("test")
