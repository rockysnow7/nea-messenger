import sqlite3
import ip
import encoding

from server import Server
from message import Message, MessageType


server = Server()

ip_addr_encoded = encoding.encode_ip_addr(ip.get_host_ip_addr())
password_hash = encoding.hash_str("password")

server.create_new_user(
    "finn",
    ip_addr_encoded,
    password_hash,
)
