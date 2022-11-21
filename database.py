import sys
import os
import shutil
import json
import sqlite3

from chat_type import ChatType
from message import Message
from constants import USERNAME_MAX_LEN, MESSAGE_CONTENT_MAX_LEN


class Database:
    def __init__(self) -> None:
        self.create_new_server_db()

        if os.path.exists("chats"):
            shutil.rmtree("chats")
        os.mkdir("chats")


    def create_new_chat(
        self,
        chat_name: str,
        chat_type: ChatType,
        public_key: int,
        members: list[str],
        admins: list[str],
    ) -> None:
        """
        Creates a new chat history table and saves the chat data in a JSON file.

        :param chat_name: the sanitised chat name
        :param public_key: the public key of the chat
        :param members: the list of usernames of users in the chat
        :param admins: the list of usernames of users in the chat with admin
        privileges
        """

        self.create_new_chat_history_table(chat_name)
        self.save_new_chat_data(chat_name, chat_type, public_key, members, admins)

    def get_all_usernames(self) -> list[str]:
        conn = sqlite3.connect("server-db.db")
        c = conn.cursor()

        c.execute("SELECT username FROM users")
        usernames = c.fetchall()

        return [username[0] for username in usernames]

    def create_new_user(
        self,
        username: str,
        ip_addr: str,
        password_hash: str,
    ) -> None:
        """
        Saves a new user into the users table.

        :param username: the sanitised username
        :param ip_addr: the 8 digit hex representation of the user's IP
        address
        :param password_hash: the 64 digit hex representation of the hash
        of the user's password
        """

        conn = sqlite3.connect("server-db.db")
        c = conn.cursor()

        c.execute(
            """
            INSERT INTO users (username, ip_addr, password_hash)
            VALUES (?, ?, ?)
            """,
            (username, ip_addr, password_hash,),
        )
        conn.commit()


    def save_new_chat_data(
        self,
        chat_name: str,
        chat_type: ChatType,
        public_key: int,
        members: list[str],
        admins: list[str],
    ) -> None:
        """
        Saves the data of a new chat to a JSON file.

        :param chat_name: the sanitised chat name
        :param chat_type: the chat type (ChatType.INDIVIDUAL or ChatType.GROUP)
        :param public_key: the public key of the chat
        :param members: the list of usernames of users in the chat
        :param admins: the list of usernames of users in the chat with admin
        privileges
        """

        data = {
            "chat-type": chat_type.value,
            "public-key": public_key,
            "members": members,
            "admins": admins,
            "nicknames": {m: m for m in members},
        }

        with open(f"chats/{chat_name}.json", "w+") as f:
            f.write(json.dumps(data, indent=4))

    def create_new_server_db(self) -> None:
        """
        Creates the server database and the users table. Should only be called
        once (each call deletes the existing database if found).
        """

        if os.path.exists("server-db.db"):
            os.remove("server-db.db")
        
        conn = sqlite3.connect("server-db.db")
        c = conn.cursor()
    
        c.execute(f"""
                  CREATE TABLE users(
                  username VARCHAR({USERNAME_MAX_LEN}) PRIMARY KEY,
                  ip_addr VARCHAR(8),
                  password_hash VARCHAR(64)
                  )
                  """)


    def create_new_chat_history_table(self, chat_name: str) -> None:
        """
        Creates a new chat history for a new chat.

        :param chat_name: the sanitised chat name
        """

        conn = sqlite3.connect("server-db.db")
        c = conn.cursor()

        c.execute(f"""
                  CREATE TABLE {chat_name}(
                  mes_purpose INT,
                  sender_username VARCHAR({USERNAME_MAX_LEN}),
                  content VARCHAR({MESSAGE_CONTENT_MAX_LEN}),
                  )
                  """)

    def save_message(self, message: Message) -> None:
        """
        Saves a message to the relevant chat history table.

        :param message: the sanitised message
        """

        conn = sqlite3.connect("server-db.db")
        c = conn.cursor()

        c.execute(
            f"""
            INSERT INTO {message.chat_name} (mes_purpose, sender_username, content)
            VALUES (?, ?, ?)
            """,
            (int(message.mes_purpose), message.sender, message.content),
        )
        conn.commit()

    def debug_display_chat_history(self, chat_name: str) -> None:
        conn = sqlite3.connect("server-db.db")
        c = conn.cursor()

        c.execute(f"SELECT * FROM {chat_name}")
        print(c.fetchall())