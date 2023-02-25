import os
import sys
import socket
import secrets
import json
import sympy
import encoding
import ip
import vernam
import rsa

from dataclasses import dataclass
from node import Client, Server
from chat_type import ChatType
from message import Message, MessagePurpose, TextData, CommandData, Data
from constants import USERNAME_MAX_LEN, MESSAGE_CONTENT_MAX_LEN
from ui_data import UIDataTopic


@dataclass
class Color:
    WHITE   = u"\u001b[37m"
    BLUE    = u"\u001b[34m"
    RESET   = u"\u001b[0m"

COLORS = {
    "white": Color.WHITE,
    "blue": Color.BLUE,
}

class UI:
    def __init__(self) -> None:
        self.client = Client()
        self.client.run()
        self.settings = {
            "color": "white",
        }
        self.is_logged_in = False

    def __print(self, message: str) -> None:
        print(COLORS[self.settings["color"]] + message + Color.RESET)

    def __input(self, message: str) -> str:
        response = input(COLORS[self.settings["color"]] + message)
        print(Color.RESET, end="")

        return response

    def __get_user_settings(self, key: str) -> any:
        self.client.send_message(Message(
            MessagePurpose.GET_SETTINGS,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(key),
        ))

        while not any(data.topic == UIDataTopic.SETTINGS for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.SETTINGS:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]

                return data.value

    def __update_settings(self) -> None:
        if not self.is_logged_in:
            return

        for key in self.settings:
            self.settings[key] = self.__get_user_settings(key)

    def __create_user(self) -> bool:
        """
        Handles account creation.

        :return: True if the account was created, False otherwise
        """

        self.__update_settings()

        username = self.__input("username: ")
        username_padded = username + "\0" * (USERNAME_MAX_LEN - len(username))
        password = self.__input("password: ")
        password_hash = encoding.hash_str(password)

        self.client.send_message(Message(
            MessagePurpose.CREATE_USER,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(username_padded + password_hash),
        ))

        while not any(data.topic == UIDataTopic.CREATE_USER for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.CREATE_USER:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                self.username = username
                return data.success

    def __log_in(self) -> None:
        """
        Handles logging in.

        :return: True if the login was successful, False otherwise
        """

        self.__update_settings()

        username = self.__input("username: ")
        username_padded = username + "\0" * (USERNAME_MAX_LEN - len(username))
        password = self.__input("password: ")
        password_hash = encoding.hash_str(password)

        mes = Message(
            MessagePurpose.TEST_LOGIN,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(username_padded + password_hash),
        )
        self.client.send_message(mes)

        while not any(data.topic == UIDataTopic.LOG_IN for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.LOG_IN:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                self.username = username
                return data.success

        self.settings["color"] = self.__get_user_settings("color")

    def __get_chat_names(self) -> list[str]:
        username = self.username + "\0" * (USERNAME_MAX_LEN - len(self.username))
        self.client.send_message(Message(
            MessagePurpose.GET_USER_CHAT_NAMES,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(username),
        ))

        while not any(data.topic == UIDataTopic.GET_USER_CHAT_NAMES for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.GET_USER_CHAT_NAMES:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                return data.value

    def __get_all_usernames(self) -> list[str]:
        self.client.send_message(Message(
            MessagePurpose.GET_ALL_USERNAMES,
            encoding.encode_ip_addr(self.client.ip_addr),
            Data(),
        ))

        while not any(data.topic == UIDataTopic.GET_ALL_USERNAMES for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.GET_ALL_USERNAMES:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                return data.value

    def __run_general_settings(self) -> None:
        """
        Allows the user to edit general settings.
        """

        self.__update_settings()

        os.system("clear")
        self.__print("GENERAL SETTINGS\n")

        while True:
            self.__print("1) go back")
            self.__print("2) change interface color")

            option = int(self.__input("> "))
            if option == 1:
                break

            if option == 2:
                while True:
                    self.__print("1) white (default)")
                    self.__print("2) blue")

                    color_option = int(self.__input("> "))
                    if color_option == 1:
                        self.client.send_message(Message(
                            MessagePurpose.SET_COLOR,
                            encoding.encode_ip_addr(self.client.ip_addr),
                            CommandData("white"),
                        ))
                        self.settings["color"] = "white"
                        break

                    elif color_option == 2:
                        self.client.send_message(Message(
                            MessagePurpose.SET_COLOR,
                            encoding.encode_ip_addr(self.client.ip_addr),
                            CommandData("blue"),
                        ))
                        self.settings["color"] = "blue"
                        break

    def __create_individual_chat_name(self, user_1: str, user_2: str) -> str:
        return "-".join(sorted([user_1, user_2]))

    def __get_ip_addr_from_username(self, username: str) -> str:
        self.client.send_message(Message(
            MessagePurpose.GET_IP_ADDR,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(username),
        ))

        while not any(data.topic == UIDataTopic.GET_IP_ADDR for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.GET_IP_ADDR:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                return encoding.decode_ip_addr(data.value)

    def __gen_vernam_key(self, ip_addr: str) -> int:
        """
        Begin the Diffie-Hellman key exchange with the client with the given IP
        address.
        """

        self.client.start_key_exchange(ip_addr)

        while not any(data.topic == UIDataTopic.VERNAM_KEY for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.VERNAM_KEY:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                return data.value

    def __send_private_key(
        self,
        priv_key: tuple[int, int],
        recipient_username: str,
        chat_name: str,
    ) -> bool:
        """
        Generates a key with the recipient by Diffie-Hellman, pairs it with the
        relevant chat name, encrypts both with Vernam, and sends it to the
        recipient.
        """

        ip_addr = self.__get_ip_addr_from_username(recipient_username)
        try:
            vernam_key = self.__gen_vernam_key(encoding.encode_ip_addr(ip_addr))
        except socket.error: # return False if the recipient is offline
            return False

        json_data = json.dumps({
            "privKey": priv_key,
            "chatName": chat_name,
        })
        encrypted_data = vernam.crypt(json_data, vernam_key)
        try:
            self.client.send_message_to_ip(Message(
                MessagePurpose.KEY,
                encoding.encode_ip_addr(self.client.ip_addr),
                CommandData(encrypted_data),
            ), ip_addr)

            return True

        except socket.error: # return False if the recipient is offline
            return False

    def __run_create_chat(self) -> None:
        """
        Allows the user to create a new chat.
        """

        self.__update_settings()

        os.system("clear")
        self.__print("CREATE CHAT\n")

        while True:
            self.__print("1) go back")
            self.__print("2) single chat")
            self.__print("3) group chat")

            type_option = int(self.__input("> "))
            if type_option == 1:
                break

            if type_option == 2:
                other_username = self.__input("\nOther person's username: ")
                all_usernames = self.__get_all_usernames()
                if other_username in all_usernames: # check if other user exists
                    chat_name = self.__create_individual_chat_name(self.username, other_username)
                    chat_names = self.__get_chat_names()
                    if chat_name not in chat_names: # check if user already has this chat
                        pub_key, priv_key = rsa.gen_keys(
                            secrets.choice(list(sympy.primerange(100, 200))),
                            secrets.choice(list(sympy.primerange(100, 200))),
                        )
                        if self.__send_private_key(
                            priv_key,
                            other_username,
                            chat_name,
                        ):
                            data = json.dumps({
                                "chat_name": chat_name,
                                "chat_type": ChatType.INDIVIDUAL.value,
                                "public_key": pub_key,
                                "members": [self.username, other_username],
                                "admins": [self.username, other_username],
                            })

                            # create chat on server
                            self.client.send_message(Message(
                                MessagePurpose.CREATE_CHAT,
                                encoding.encode_ip_addr(self.client.ip_addr),
                                CommandData(data),
                            ))

                            # save private key locally
                            if not os.path.exists("user-chats"):
                                os.mkdir("user-chats")

                            with open(f"user-chats/{chat_name}.json", "w+") as f:
                                data = json.dump({
                                    "privKey": priv_key,
                                }, f, indent=4)

                            self.__print("Created chat!")
                        else:
                            self.__print("Other user is offline, please try again later.")

                    else:
                        self.__print(f"You already have a chat with {other_username}!\n")
                else:
                    self.__print("That user does not exist.")

            elif type_option == 3:
                chat_name = self.__input("\nChat name: ")
                chat_names = self.__get_chat_names()
                if chat_name not in chat_names:
                    all_usernames = self.__get_all_usernames()
                    other_usernames = []
                    i = 1
                    while True:
                        other = self.__input(f"Other user {i} (leave blank to stop): ")
                        if not other:
                            break

                        if other in all_usernames:
                            other_usernames.append(other)
                            i += 1
                        else:
                            self.__print("This user does not exist!")

                    pub_key, priv_key = rsa.gen_keys(
                        secrets.choice(list(sympy.primerange(100, 200))),
                        secrets.choice(list(sympy.primerange(100, 200))),
                    )

                    added = []
                    for username in other_usernames:
                        if self.__send_private_key(
                            priv_key,
                            username,
                            chat_name,
                        ):
                            added.append(username)

                    if added:
                        for username in other_usernames:
                            if username not in added:
                                self.__print(f"{username} is offline, try adding them later!")

                        data = json.dumps({
                            "chat_name": chat_name,
                            "chat_type": ChatType.GROUP.value,
                            "public_key": pub_key,
                            "members": [self.username] + added,
                            "admins": [self.username],
                        })
                        self.client.send_message(Message(
                            MessagePurpose.CREATE_CHAT,
                            encoding.encode_ip_addr(self.client.ip_addr),
                            CommandData(data),
                        ))

                        if not os.path.exists("user-chats"):
                            os.mkdir("user-chats")

                        with open(f"user-chats/{chat_name}.json", "w+") as f:
                            data = json.dump({
                                "privKey": priv_key,
                            }, f, indent=4)

                        self.__print("Created chat!")
                    else:
                        self.__print("All users were offline, please try again later.")
                else:
                    self.__print("You already have a chat with that name!\n")

    def __run_chat(self, chat_name: str) -> None:
        """
        Allows the user to interact with a chat.
        """

        self.__update_settings()

        os.system("clear")
        self.__print(f"{chat_name}\n")

        ...

    def __run_main_menu(self) -> None:
        """
        Allows the user to select a chat or edit general settings.
        """

        self.__update_settings()

        os.system("clear")
        self.__print("MAIN MENU\n")

        while True:
            self.__print("1) log out")
            self.__print("2) edit general settings")
            self.__print("3) create new chat")

            user_chats = self.__get_chat_names()
            for i in range(len(user_chats)):
                self.__print(f"{i+4}) view {user_chats[i]}")

            option = int(self.__input("> "))

            if option == 1:
                break

            if option == 2:
                self.__run_general_settings()

            elif option == 3:
                self.__run_create_chat()

            elif option <= len(user_chats) - 3:
                self.__run_chat(user_chats[option - 3])

    def run_login_page(self) -> None:
        """
        Entry point. Allows the user to create an account or log in to an
        existing one.
        """

        self.__update_settings()

        os.system("clear")
        self.__print("SIGN UP OR LOG IN\n")

        while True:
            self.__print("1) exit")
            self.__print("2) sign up")
            self.__print("3) log in")
            option = int(self.__input("> "))

            if option == 1:
                self.client.is_running = False
                break

            elif option == 2:
                if self.__create_user():
                    self.is_logged_in = True
                    self.__print("\nCreated user!\n")
                    self.__run_main_menu()
                else:
                    self.__print("\nUsername already taken, please choose a different username.\n")

            elif option == 3:
                if self.__log_in():
                    self.is_logged_in = True
                    self.__print("\nLogged in!\n")
                    self.__run_main_menu()
                else:
                    self.__print("\nUsername or password is wrong, please try again.\n")
