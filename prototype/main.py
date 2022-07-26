import sqlite3
import ip
import encoding

from database import Database, ChatType
from message import Message, MessageType


db = Database()

db.create_new_user(
    "finn",
    ip.get_host_ip_addr(),
    encoding.hash_str("password"),
)
db.create_new_user(
    "other",
    ip.get_host_ip_addr(),
    encoding.hash_str("1234"),
)

db.create_new_chat(
    "finn_other",
    ChatType.INDIVIDUAL,
    1234,
    ["finn", "other"],
    ["finn", "other"],
)

db.save_message(Message(
    MessageType.TEXT,
    "hey hey",
    "finn",
    "finn_other",
))
