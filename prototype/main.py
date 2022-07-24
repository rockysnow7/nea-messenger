import sqlite3
import socket

from server import Server
from message import Message, MessageType


server = Server()

server.create_new_user(
    "finn",
    socket.gethostbyname(socket.gethostname()),
    hash("password"),
)
