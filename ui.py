import os
import encoding
import ip

from dataclasses import dataclass
from node import Client, Server
from message import Message, MessagePurpose, TextData, CommandData
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

    def __send_message(self) -> None:
        sender = self.__input("sender: ")
        chat = self.__input("chat: ")
        content = TextData(self.__input("content: "))

        mes = Message(
            MessagePurpose.MESSAGE,
            sender,
            chat,
            content,
        )
        self.client.send_message(mes)

    def __create_user(self) -> bool:
        """
        Handles account creation.

        :return: True if the account was created, False otherwise
        """

        self.__update_settings()

        username = self.__input("username: ")
        username += "\0" * (USERNAME_MAX_LEN - len(username))
        password = self.__input("password: ")
        password_hash = encoding.hash_str(password)

        mes = Message(
            MessagePurpose.CREATE_USER,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(username + password_hash),
        )
        self.client.send_message(mes)

        while not any(data.topic == UIDataTopic.CREATE_USER for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.CREATE_USER:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                self.username = username
                self.is_logged_in = True
                return data.success

    def __log_in(self) -> None:
        """
        Handles logging in.

        :return: True if the login was successful, False otherwise
        """

        self.__update_settings()

        username = self.__input("username: ")
        username += "\0" * (USERNAME_MAX_LEN - len(username))
        password = self.__input("password: ")
        password_hash = encoding.hash_str(password)

        mes = Message(
            MessagePurpose.TEST_LOGIN,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(username + password_hash),
        )
        self.client.send_message(mes)

        while not any(data.topic == UIDataTopic.LOG_IN for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.LOG_IN:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                self.username = username
                self.is_logged_in = True
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

        user_chats = self.__get_chat_names()

        os.system("clear")
        self.__print("MAIN MENU\n")

        while True:
            self.__print("1) log out")
            self.__print("2) edit general settings")
            self.__print("3) create new chat")
            for i in range(len(user_chats)):
                self.__print(f"{i+4}) view {user_chats[i]}")

            option = int(self.__input("> "))

            if option == 1:
                break

            if option == 2:
                self.__run_general_settings()

            elif option == 3:
                ...

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
                    self.__print("\nCreated user!\n")
                    self.__run_main_menu()
                else:
                    self.__print("\nUsername already taken, please choose a different username.\n")

            elif option == 3:
                if self.__log_in():
                    self.__print("\nLogged in!\n")
                    self.__run_main_menu()
                else:
                    self.__print("\nUsername or password is wrong, please try again.\n")
