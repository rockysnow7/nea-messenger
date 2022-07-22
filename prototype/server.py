import os
import json
import sqlite3

from sqlite3 import Error
from message import Message


USERNAME_MAX_LEN = 20
MESSAGE_CONTENT_MAX_LEN = 500


class Server:
	def __init__(self):
		self.create_new_server_db()
		if not os.path.exists("chats"):
			os.mkdir("chats")

			
	def create_new_chat(self, chat_name, public_key, members, admins):
		self.create_new_chat_history_table(chat_name)
		self.save_chat_data(chat_name, public_key, members, admins)

	def save_chat_data(self, chat_name, public_key, members, admins):
		data = {
			"public-key": public_key,
			"members": members,
			"admins": admins,
		}

		with open(f"chats/{chat_name}.json", "w+") as f:
			f.write(json.dumps(data, indent=4))

			
	def create_new_server_db(self):
		if os.path.exists("server-db.db"):
			os.remove("server-db.db")
		
		conn = sqlite3.connect("server-db.db")
		c = conn.cursor()
	
		c.execute(f"""
				  CREATE TABLE users(
				  username VARCHAR({USERNAME_MAX_LEN}) PRIMARY KEY,
				  ip_addr VARCHAR(32),
				  password_hash VARCHAR(32)
				  )
				  """)
    
	def create_new_chat_history_table(self, chat_name):
		conn = sqlite3.connect("server-db.db")
		c = conn.cursor()
	
		c.execute(f"""
				  CREATE TABLE {chat_name}(
				  id INT AUTO_INCREMENT,
				  message_type INT,
				  content VARCHAR({MESSAGE_CONTENT_MAX_LEN}),
				  sender_username VARCHAR({USERNAME_MAX_LEN})
				  )
				  """)

	def save_message(self, message):
		conn = sqlite3.connect("server-db.db")
		c = conn.cursor()

		c.execute(f"""
				  INSERT INTO {message.chat_name} (message_type, content, sender_username)
				  VALUES ({message.message_type.value}, '{message.content}', '{message.sender_username}')
				  """)

	def debug_display_chat_history(self, chat_name):
		conn = sqlite3.connect("server-db.db")
		c = conn.cursor()
	
		c.execute(f"SELECT * FROM {chat_name}")
		print(c.fetchall())
