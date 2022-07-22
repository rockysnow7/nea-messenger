import sqlite3

from server import Server
from message import Message, MessageType


server = Server()

server.create_new_server_db()
server.create_new_chat("test", 1234, ["finn", "other"], ["finn"])
server.save_message(Message(MessageType.TEXT, "Hello, world!", "finn", "test"))
server.debug_display_chat_history("test")

# conn = sqlite3.connect("server-db.db")
# c = conn.cursor()

# c.execute("SELECT * FROM test WHERE id = 0")
# print(c.fetchall())
