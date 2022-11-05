import encoding
import ip

from node import Client, Server
from message import Message, MessagePurpose, TextData, CommandData
from database import USERNAME_MAX_LEN, MESSAGE_CONTENT_MAX_LEN


class UI:
    def __init__(self, server: Server) -> None:
        self.client = Client(server)

    def _send_message(self) -> None:
        sender = input("sender: ")
        chat = input("chat: ")
        content = TextData(input("content: "))

        mes = Message(
            MessagePurpose.MESSAGE,
            sender,
            chat,
            content,
        )
        self.client.send_message(mes)

    def _create_user(self) -> None:
        username = input("username: ")
        username += "\0" * (USERNAME_MAX_LEN - len(username))
        password = input("password: ")
        password_hash = encoding.hash_str(password)

        mes = Message(
            MessagePurpose.CREATE_USER,
            encoding.encode_ip_addr(ip.get_host_ip_addr()),
            CommandData(username + password_hash),
        )
        self.client.send_message(mes)

    def main_loop(self) -> None:
        """
        Main program loop.
        """

        while True:
            print("1) create account")
            print("2) send message")
            option = int(input("> "))

            if option == 1:
                self._create_user()
