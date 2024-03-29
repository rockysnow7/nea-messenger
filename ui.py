import os
import sys
import time
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
from constants import USERNAME_MAX_LEN, CHAT_NAME_MAX_LEN, MESSAGE_CONTENT_MAX_LEN, VALID_NAME_CHARS
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

    def __print_with_delay(self, message: str, delay: float = 0.5) -> None:
        self.__print(message)
        time.sleep(delay)

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

    def __create_user(self) -> tuple[bool, str]:
        """
        Handles account creation.

        :return: True if the account was created, False otherwise
        """

        self.__update_settings()

        username = self.__input("username: ")
        if len(username) > USERNAME_MAX_LEN:
            return False, f"\nUsername is too long, please use a maximum of {USERNAME_MAX_LEN} characters.\n"

        if any(c for c in username if c not in VALID_NAME_CHARS):
            return False, f"\nUsername contains invalid characters, please only use letters or digits.\n"

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
                return data.success, "\nUsername already taken, please choose a different username. If this issue persists, you may already have an account under this IP address, and will need to log into that account.\n"

    def __log_in(self) -> bool:
        """
        Handles logging in.

        :return: True if the login was successful, False otherwise
        """

        self.__update_settings()

        username = self.__input("username: ")
        if len(username) > USERNAME_MAX_LEN \
        or any(c for c in username if c not in VALID_NAME_CHARS):
            return False

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

    def __get_chat_data(self, chat_name: str) -> dict[str, any]:
        self.client.send_message(Message(
            MessagePurpose.GET_CHAT_DATA,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(chat_name),
        ))

        while not any(data.topic == UIDataTopic.GET_CHAT_DATA for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.GET_CHAT_DATA:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                return data.value

    def __get_chat_messages(
        self,
        chat_name: str,
        num_messages: int,
    ) -> list[Message]:
        data = json.dumps({
            "chatName": chat_name,
            "numMessages": num_messages,
        })

        self.client.send_message(Message(
            MessagePurpose.GET_CHAT_MESSAGES,
            encoding.encode_ip_addr(self.client.ip_addr),
            CommandData(data),
        ))

        while not any(data.topic == UIDataTopic.GET_CHAT_MESSAGES for data in self.client.ui_data):
            pass

        for i in range(len(self.client.ui_data)):
            if self.client.ui_data[i].topic == UIDataTopic.GET_CHAT_MESSAGES:
                data = self.client.ui_data[i]
                del self.client.ui_data[i]
                break

        if not os.path.exists(f"user-chats/{chat_name}.json"):
            return []

        with open(f"user-chats/{chat_name}.json", "r") as f:
            priv_key = json.load(f)
        priv_key = tuple(priv_key["privKey"])

        messages = data.value
        for i in range(len(messages)):
            messages[i] = rsa.decrypt(messages[i], priv_key)

        return messages

    def __run_general_settings(self) -> None:
        """
        Allows the user to edit general settings.
        """

        self.__update_settings()

        while True:
            os.system("clear")
            self.__print("GENERAL SETTINGS\n")
            self.__print("1) go back")
            self.__print("2) change interface color")

            option = self.__input("> ")
            if option == "1":
                break

            if option == "2":
                while True:
                    self.__print("1) white (default)")
                    self.__print("2) blue")

                    color_option = self.__input("> ")
                    if color_option == "1":
                        self.client.send_message(Message(
                            MessagePurpose.SET_COLOR,
                            encoding.encode_ip_addr(self.client.ip_addr),
                            CommandData("white"),
                        ))
                        self.settings["color"] = "white"
                        break

                    elif color_option == "2":
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
        except socket.print_with_delay: # return False if the recipient is offline
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

        except socket.print_with_delay: # return False if the recipient is offline
            return False

    def __run_create_chat(self) -> None:
        """
        Allows the user to create a new chat.
        """

        self.__update_settings()

        while True:
            os.system("clear")
            self.__print("CREATE CHAT\n")
            self.__print("1) go back")
            self.__print("2) single chat")
            self.__print("3) group chat")

            type_option = self.__input("> ")
            if type_option == "1":
                break

            if type_option == "2":
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

                            self.__print_with_delay("\nCreated chat!\n")
                        else:
                            self.__print_with_delay("\nOther user is offline, please try again later.")
                    else:
                        self.__print_with_delay(f"\nYou already have a chat with {other_username}!\n")
                else:
                    self.__print_with_delay("\nThat user does not exist.")

            elif type_option == "3":
                chat_name = self.__input("\nChat name: ")
                if len(chat_name) > CHAT_NAME_MAX_LEN:
                    self.__print_with_delay(f"\nChat name is too long, please use a maximum of {CHAT_NAME_MAX_LEN} characters.\n")
                    continue

                if any(c for c in chat_name if c not in VALID_NAME_CHARS):
                    self.__print_with_delay("\nChat name has invalid characters, please only use letters or digits.\n")
                    continue

                chat_names = self.__get_chat_names()
                if chat_name not in chat_names:
                    all_usernames = self.__get_all_usernames()
                    other_usernames = []
                    i = 1
                    while True:
                        other = self.__input(f"\nOther user {i} (leave blank to stop): ")
                        if not other:
                            break

                        if other in all_usernames:
                            other_usernames.append(other)
                            i += 1
                        else:
                            self.__print("\nThis user does not exist!")

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

                        self.__print_with_delay("\nCreated chat!\n")
                    else:
                        self.__print_with_delay("\nAll users were offline, please try again later.")
                else:
                    self.__print_with_delay("\nYou already have a chat with that name!\n")

    def __format_messages(
        self,
        messages: list[Message],
        chat_data: dict[str, any],
    ) -> list[str]:
        cols, rows = os.get_terminal_size(0)
        lines = []
        for message in messages:
            message_lines = [
                f"[{chat_data['nicknames'][message.sender]}] {message.content.value}"
            ]
            views = [chat_data["nicknames"][name] for name in message.views if name]
            if views:
                views = ", ".join(views)
                message_lines[0] += f"\t[seen by {views}]"

            if len(message_lines[0]) > cols:
                message_lines.append(message_lines[0][cols:])
                message_lines[0] = message_lines[0][:cols]
            lines += message_lines

        # leave 5 lines at bottom, also account for 2 already printed at top
        NUM_CLEAR_LINES = 10
        lines = lines[-rows:] + ["" for _ in range(rows - len(lines) - NUM_CLEAR_LINES - 2)]

        return lines

    def __run_chat_admin_settings(
        self,
        chat_name: str,
    ) -> None:
        """
        Allows the user to edit a chat's admin settings.
        """

        self.__update_settings()

        while True:
            chat_data = self.__get_chat_data(chat_name)

            os.system("clear")
            self.__print("CHAT ADMIN SETTINGS\n")
            self.__print("1) go back")
            self.__print("2) set privilege level of another user")
            self.__print("3) add user to chat")
            self.__print("4) remove user from chat")

            option = self.__input("> ")
            if option == "1":
                break

            if option == "2":
                username = self.__input("Username: ")
                if username in chat_data["members"]:
                    level = self.__input("Level (regular or admin): ")
                    if level == "regular":
                        if username in chat_data["admins"]:
                            data = json.dumps({
                                "chatName": chat_name,
                                "username": username,
                                "level": level,
                            })
                            self.client.send_message(Message(
                                MessagePurpose.SET_PRIVILEGE,
                                encoding.encode_ip_addr(self.client.ip_addr),
                                CommandData(data),
                            ))
                        else:
                            self.__print_with_delay(f"\n{username} is already a regular user.\n")

                    elif level == "admin":
                        if username in chat_data["admins"]:
                            self.__print_with_delay(f"\n{username} is already an admin.\n")
                        else:
                            data = json.dumps({
                                "chatName": chat_name,
                                "username": username,
                                "level": level,
                            })
                            self.client.send_message(Message(
                                MessagePurpose.SET_PRIVILEGE,
                                encoding.encode_ip_addr(self.client.ip_addr),
                                CommandData(data),
                            ))
                            self.__print_with_delay("\nChanged privilege.\n")

                    else:
                        self.__print_with_delay("\nPlease choose a valid option.\n")
                else:
                    self.__print_with_delay("\nThat user is not in this chat.\n")

            elif option == "3":
                username = self.__input("Username: ")
                if username in self.__get_all_usernames():
                    if username not in chat_data["members"]:
                        with open(f"user-chats/{chat_name}.json", "r") as f:
                            priv_key = json.load(f)
                        priv_key = tuple(priv_key["privKey"])

                        if self.__send_private_key(
                            priv_key,
                            username,
                            chat_name,
                        ):
                            data = json.dumps({
                                "chatName": chat_name,
                                "username": username,
                            })
                            self.client.send_message(Message(
                                MessagePurpose.ADD_USER_TO_CHAT,
                                encoding.encode_ip_addr(self.client.ip_addr),
                                CommandData(data),
                            ))
                            self.__print_with_delay(f"\nUser added.\n")
                    else:
                        self.__print_with_delay(f"\nThat user is already in this chat.\n")
                else:
                    self.__print_with_delay(f"\nThat user does not exist!\n")

            elif option == "4":
                username = self.__input("Username: ")
                if username in self.__get_all_usernames():
                    if username in chat_data["members"]:
                        data = json.dumps({
                            "chatName": chat_name,
                            "username": username,
                        })
                        self.client.send_message(Message(
                            MessagePurpose.REMOVE_USER_FROM_CHAT,
                            encoding.encode_ip_addr(self.client.ip_addr),
                            CommandData(data),
                        ))
                        self.__print_with_delay(f"\nUser removed.\n")
                    else:
                        self.__print_with_delay(f"\nThat user is not in this chat.\n")
                else:
                    self.__print_with_delay(f"\nThat user does not exist!\n")

            else:
                self.__print_with_delay("\nPlease choose a valid option.\n")

    def __run_chat_settings(
        self,
        chat_name: str,
    ) -> None:
        """
        Allows the user to edit a chat's settings.
        """

        self.__update_settings()

        while True:
            chat_data = self.__get_chat_data(chat_name)

            os.system("clear")
            self.__print("CHAT SETTINGS\n")
            self.__print("1) go back")
            self.__print("2) edit someone's nickname")
            if ChatType(chat_data["chatType"]) == ChatType.GROUP \
            and self.username in chat_data["admins"]:
                self.__print("3) admin settings")

            option = self.__input("> ")
            if option == "1":
                break

            if option == "2":
                username = self.__input("Username: ")
                if username in chat_data["members"]:
                    nickname = self.__input("Nickname: ")
                    if nickname not in chat_data["nicknames"].values():
                        if len(nickname) > USERNAME_MAX_LEN:
                            self.__print_with_delay(f"\nNickname is too long, please use a maximum of {USERNAME_MAX_LEN} characters.\n")
                            continue

                        if any(c for c in nickname if c not in VALID_NAME_CHARS):
                            self.__print_with_delay("\nUsername contains invalid characters, please only use letters or digits.\n")
                            continue

                        data = json.dumps({
                            "chatName": chat_name,
                            "username": username,
                            "nickname": nickname,
                        })
                        self.client.send_message(Message(
                            MessagePurpose.SET_NICKNAME,
                            encoding.encode_ip_addr(self.client.ip_addr),
                            CommandData(data),
                        ))
                        self.__print_with_delay("\nChanged nickname.\n")
                    else:
                        self.__print_with_delay("\nSomeone already has that name, please choose another one.\n")
                else:
                    self.__print_with_delay("\nThat user isn't in this chat!\n")

            elif option == "3" \
            and ChatType(chat_data["chatType"]) == ChatType.GROUP \
            and self.username in chat_data["admins"]:
                self.__run_chat_admin_settings(chat_name)

            else:
                self.__print_with_delay("\nPlease enter a valid option.\n")

    def __run_chat(self, chat_name: str) -> None:
        """
        Allows the user to interact with a chat.
        """

        self.__update_settings()

        while True:
            os.system("clear")
            self.__print(f"{chat_name}\n")

            chat_data = self.__get_chat_data(chat_name)
            messages = self.__get_chat_messages(chat_name, 10)
            for line in self.__format_messages(messages, chat_data):
                self.__print(line)

            self.__print("\n1) go back")
            self.__print("2) send message")
            self.__print("3) refresh")
            self.__print("4) edit chat settings")

            option = self.__input("> ")
            if option == "1":
                break

            if option == "2":
                message = self.__input("Message (leave blank to cancel): ").strip()
                if message:
                    if len(message) <= MESSAGE_CONTENT_MAX_LEN:
                        self.client.send_message(Message(
                            MessagePurpose.MESSAGE,
                            encoding.encode_ip_addr(self.client.ip_addr),
                            TextData(message),
                            chat_name=chat_name,
                        ), tuple(chat_data["pubKey"]))
                    else:
                        self.__print_with_delay(f"\nMessage is too long, please use a maximum of {MESSAGE_CONTENT_MAX_LEN} characters.\n")

            elif option == "3":
                continue

            elif option == "4":
                self.__run_chat_settings(chat_name)

            else:
                self.__print_with_delay("\nPlease enter a valid option.\n")

    def __run_main_menu(self) -> None:
        """
        Allows the user to select a chat or edit general settings.
        """

        self.__update_settings()

        while True:
            os.system("clear")
            self.__print("MAIN MENU\n")
            self.__print("1) log out")
            self.__print("2) edit general settings")
            self.__print("3) create new chat")

            user_chats = self.__get_chat_names()
            for i in range(len(user_chats)):
                self.__print(f"{i+4}) view {user_chats[i]}")

            option = self.__input("> ")

            if option == "1":
                break

            if option == "2":
                self.__run_general_settings()

            elif option == "3":
                self.__run_create_chat()

            elif option.isdigit() and int(option) - 4 < len(user_chats):
                self.__run_chat(user_chats[int(option) - 4])

            else:
                self.__print_with_delay("\nPlease enter a valid option.\n")

    def run_login_page(self) -> None:
        """
        Entry point. Allows the user to create an account or log in to an
        existing one.
        """

        self.__update_settings()

        while True:
            os.system("clear")
            self.__print("SIGN UP OR LOG IN\n")
            self.__print("1) exit")
            self.__print("2) sign up")
            self.__print("3) log in")
            option = self.__input("> ")

            if option == "1":
                self.client.is_running = False
                break

            elif option == "2":
                success, error_message = self.__create_user()
                if success:
                    self.is_logged_in = True
                    self.__print_with_delay("\nCreated user!\n")
                    self.__run_main_menu()
                else:
                    self.__print_with_delay(error_message, 1)

            elif option == "3":
                if self.__log_in():
                    self.is_logged_in = True
                    self.__print_with_delay("\nLogged in!\n")
                    self.__run_main_menu()
                else:
                    self.__print_with_delay("\nUsername or password is wrong, please try again.\n")
