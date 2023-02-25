import os
import sys
import socket
import threading
import time
import json
import sympy
import secrets
import ip
import encoding
import database
import vernam

from typing import Callable
from datetime import datetime
from message import Message, MessagePurpose, Data, TextData, CommandData
from chat_type import ChatType
from constants import USERNAME_MAX_LEN
from math_funcs import primitive_root_mod
from rsa import rsa_encrypt, rsa_decrypt
from ui_data import UIData, UIDataTopic


SERVER_IP_ADDR = "192.168.0.35"

CLIENT_SEND_PORT = 8000
SERVER_SEND_PORT = 8001
CLIENT_RECV_PORT = 8002
SERVER_RECV_PORT = 8003

KEY_MIN = 500
KEY_MAX = 1000


class Node:
    def __init__(self, is_client: bool) -> None:
        self.ip_addr = ip.get_host_ip_addr()
        self.is_running = False
        self._recvd_messages = []

        self.__recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__recv_socket.bind((self.ip_addr, CLIENT_RECV_PORT if is_client else SERVER_RECV_PORT))

    @property
    def recvd_messages(self) -> list[Message]:
        return self._recvd_messages

    def _send_bytes_to_ip(self, ip_addr: str, data: bytes, recipient_is_client: bool) -> None:
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((ip_addr, CLIENT_RECV_PORT if recipient_is_client else SERVER_RECV_PORT))
        send_socket.sendall(data)
        send_socket.close()

    def _listen_loop(self, handler_method: Callable[[Message], None]) -> None:
        self.__recv_socket.listen()
        while self.is_running:
            conn, addr = self.__recv_socket.accept()
            with conn:
                data = conn.recv(1044)
                if data:
                    mes = Message.from_bytes(data)
                    handler_method(mes)

class Client(Node):
    def __init__(self) -> None:
        super().__init__(True)
        self.__time_last_checked_new_messages = 0
        self.__diffie_hellman_keys = {}
        self.ui_data = []

    def send_message(self, mes: Message, encrypt: bool = False) -> None:
        """
        Sends `mes` to the server to be handled.
        """

        if encrypt:
            mes = rsa_encrypt(mes)
        self._send_bytes_to_ip(SERVER_IP_ADDR, bytes(mes), False)

    def send_message_to_ip(self, mes: Message, ip_addr: str) -> None:
        self._send_bytes_to_ip(ip_addr, bytes(mes), True)

    def start_key_exchange(self, ip_addr: str) -> None: # alice
        """
        Initiates the Diffie-Hellman key exchange.
        """

        self.__diffie_hellman_keys[ip_addr] = {}
        p = secrets.choice(list(sympy.primerange(KEY_MIN, KEY_MAX)))
        g = primitive_root_mod(p)
        a = secrets.choice(range(1000))
        A = pow(g, a, p)

        self.__diffie_hellman_keys[ip_addr] = {
            "p": p,
            "g": g,
            "a": a,
            "A": A,
        }
        keys = json.dumps({
            "step": 1,
            "p": p,
            "g": g,
            "A": A,
        })

        self.send_message_to_ip(Message(
            MessagePurpose.EXCHANGE,
            encoding.encode_ip_addr(self.ip_addr),
            CommandData(keys),
        ), encoding.decode_ip_addr(ip_addr))

    """
    0. Alice generates p, g, a, A. Sends p, g, A to Bob (1).
    1. Bob generates b, B, s. Sends B to Alice (2).
    2. Alice generates s.

    E.g.
    0. Alice: p=23, g=5, a=7, A=17, Alice -> Bob (p, g, A)
    1. Bob: b=9, B=11, s=7, Bob -> Alice (B,)
    2. Alice: s=7
    """

    def __handle_key_exchange(self, mes: Message) -> None:
        """
        Handles the Diffie-Hellman key exchange after it is initialised.
        """

        ip_addr = mes.sender
        keys = json.loads(mes.content.value)

        if keys["step"] == 1: # bob
            self.__diffie_hellman_keys[ip_addr] = {}
            self.__diffie_hellman_keys[ip_addr]["p"] = keys["p"]
            self.__diffie_hellman_keys[ip_addr]["g"] = keys["g"]
            self.__diffie_hellman_keys[ip_addr]["A"] = keys["A"]

            self.__diffie_hellman_keys[ip_addr]["b"] = secrets.choice(range(KEY_MIN, KEY_MAX))
            self.__diffie_hellman_keys[ip_addr]["B"] = pow(
                self.__diffie_hellman_keys[ip_addr]["g"],
                self.__diffie_hellman_keys[ip_addr]["b"],
                self.__diffie_hellman_keys[ip_addr]["p"],
            )
            self.__diffie_hellman_keys[ip_addr]["s"] = pow(
                self.__diffie_hellman_keys[ip_addr]["A"],
                self.__diffie_hellman_keys[ip_addr]["b"],
                self.__diffie_hellman_keys[ip_addr]["p"],
            )
            self.send_message_to_ip(Message(
                MessagePurpose.EXCHANGE,
                encoding.encode_ip_addr(self.ip_addr),
                CommandData(json.dumps({
                    "step": 2,
                    "B": self.__diffie_hellman_keys[ip_addr]["B"],
                })),
            ), encoding.decode_ip_addr(ip_addr))

        elif keys["step"] == 2: # alice
            self.__diffie_hellman_keys[ip_addr]["B"] = keys["B"]
            self.__diffie_hellman_keys[ip_addr]["s"] = pow(
                self.__diffie_hellman_keys[ip_addr]["B"],
                self.__diffie_hellman_keys[ip_addr]["a"],
                self.__diffie_hellman_keys[ip_addr]["p"],
            )
            self.ui_data.append(UIData(
                UIDataTopic.VERNAM_KEY,
                True,
                self.__diffie_hellman_keys[ip_addr]["s"],
            ))

    def __handle_message(self, mes: Message) -> None:
        if mes.mes_purpose == MessagePurpose.EXCHANGE:
            self.__handle_key_exchange(mes)

        elif mes.mes_purpose == MessagePurpose.KEY:
            encrypted_data = mes.content.value
            sender_ip = mes.sender
            decrypted_data = json.loads(vernam.crypt(
                encrypted_data,
                self.__diffie_hellman_keys[sender_ip]["s"],
            ))

            # save private key locally
            if not os.path.exists("user-chats"):
                os.mkdir("user-chats")

            with open(f"user-chats/{decrypted_data['chatName']}.json", "w+") as f:
                data = json.dump({
                    "privKey": decrypted_data["privKey"],
                }, f, indent=4)

        elif mes.mes_purpose == MessagePurpose.CREATE_USER_DONE:
            self.ui_data.append(UIData(UIDataTopic.CREATE_USER, True))

        elif mes.mes_purpose == MessagePurpose.CREATE_USER_USERNAME_TAKEN:
            self.ui_data.append(UIData(UIDataTopic.CREATE_USER, False))

        elif mes.mes_purpose == MessagePurpose.TEST_LOGIN_SUCCESS:
            self.ui_data.append(UIData(UIDataTopic.LOG_IN, True))

        elif mes.mes_purpose == MessagePurpose.TEST_LOGIN_FAILURE:
            self.ui_data.append(UIData(UIDataTopic.LOG_IN, False))

        elif mes.mes_purpose == MessagePurpose.GET_USER_CHAT_NAMES:
            user_chat_names = json.loads(mes.content.value)
            self.ui_data.append(UIData(UIDataTopic.GET_USER_CHAT_NAMES, True, user_chat_names))

        elif mes.mes_purpose == MessagePurpose.GET_SETTINGS:
            self.ui_data.append(UIData(UIDataTopic.SETTINGS, True, mes.content.value))

        elif mes.mes_purpose == MessagePurpose.GET_ALL_USERNAMES:
            usernames = json.loads(mes.content.value)
            self.ui_data.append(UIData(UIDataTopic.GET_ALL_USERNAMES, True, usernames))

        elif mes.mes_purpose == MessagePurpose.GET_IP_ADDR:
            ip_addr = mes.content.value
            self.ui_data.append(UIData(UIDataTopic.GET_IP_ADDR, True, ip_addr))

        else:
            raise ValueError(f"Invalid MessagePurpose \"{mes.mes_purpose=}\".")

    def run(self) -> None:
        self.is_running = True
        threading.Thread(
            target=self._listen_loop,
            args=(self.__handle_message,),
        ).start()

    def exit(self) -> None:
        self.is_running = False
        print("exiting")
        sys.exit(0)

class Server(Node):
    def __init__(self) -> None:
        super().__init__(False)

        if not os.path.exists("settings"):
            os.mkdir("settings")

        self.__db = database.Database()
        self.__db.create_new_user(
            "finn",
            encoding.encode_ip_addr(SERVER_IP_ADDR),
            encoding.hash_str("test"),
        )
        self.__db.create_new_user(
            "other",
            encoding.encode_ip_addr("192.168.0.12"), # phone
            encoding.hash_str("test"),
        )

    def __send_message(self, mes: Message, recipient_ip: str) -> None:
        self._send_bytes_to_ip(recipient_ip, bytes(mes), True)

    def __handle_message(self, mes: Message) -> None:
        # save message
        if mes.mes_purpose == MessagePurpose.MESSAGE:
            self.__db.save_message(mes)

        # create an account
        elif mes.mes_purpose == MessagePurpose.CREATE_USER:
            ip_addr = mes.sender
            username = mes.content.value[:USERNAME_MAX_LEN].split("\0")[0]
            password_hash = mes.content.value[database.USERNAME_MAX_LEN:database.USERNAME_MAX_LEN + 64]

            if username not in self.__db.get_all_usernames():
                self.__db.create_new_user(username, ip_addr, password_hash)
                self.__send_message(Message(
                    MessagePurpose.CREATE_USER_DONE,
                    self.ip_addr,
                    Data(),
                ), encoding.decode_ip_addr(ip_addr))
            else:
                self.__send_message(Message(
                    MessagePurpose.CREATE_USER_USERNAME_TAKEN,
                    self.ip_addr,
                    Data(),
                ), encoding.decode_ip_addr(ip_addr))

        # create a chat
        elif mes.mes_purpose == MessagePurpose.CREATE_CHAT:
            ip_addr = mes.sender
            data = json.loads(mes.content.value)
            data["chat_type"] = ChatType(data["chat_type"])
            self.__db.create_new_chat(*data.values())

        # check if the user successfully logged in
        elif mes.mes_purpose == MessagePurpose.TEST_LOGIN:
            ip_addr = mes.sender
            username = mes.content.value[:USERNAME_MAX_LEN].split("\0")[0]
            password_hash = mes.content.value[database.USERNAME_MAX_LEN:database.USERNAME_MAX_LEN + 64]

            success = self.__db.test_username_password_hash_match(username, password_hash)
            self.__send_message(Message(
                MessagePurpose.TEST_LOGIN_SUCCESS if success else MessagePurpose.TEST_LOGIN_FAILURE,
                self.ip_addr,
                Data(),
            ), encoding.decode_ip_addr(ip_addr))

        # get a list of names of all chats the user can access
        elif mes.mes_purpose == MessagePurpose.GET_USER_CHAT_NAMES:
            ip_addr = mes.sender
            username = mes.content.value.split("\0")[0]

            user_chat_names = self.__db.get_user_chat_names(username)
            user_chat_names = json.dumps(user_chat_names)

            self.__send_message(Message(
                MessagePurpose.GET_USER_CHAT_NAMES,
                self.ip_addr,
                CommandData(user_chat_names),
            ), encoding.decode_ip_addr(ip_addr))

        # set the user's color scheme to a given color
        elif mes.mes_purpose == MessagePurpose.SET_COLOR:
            ip_addr = mes.sender
            color = mes.content.value.split("\0")[0]
            username = self.__db.get_username_from_ip_addr(ip_addr)

            self.__db.save_user_settings(username, color=color)

        # get the user's general settings
        elif mes.mes_purpose == MessagePurpose.GET_SETTINGS:
            ip_addr = mes.sender
            key = mes.content.value.split("\0")[0]
            username = self.__db.get_username_from_ip_addr(ip_addr)

            user_settings = self.__db.get_user_settings(username)
            setting = user_settings[key]

            self.__send_message(Message(
                MessagePurpose.GET_SETTINGS,
                self.ip_addr,
                CommandData(setting),
            ), encoding.decode_ip_addr(ip_addr))

        # get a list of all usernames
        elif mes.mes_purpose == MessagePurpose.GET_ALL_USERNAMES:
            ip_addr = mes.sender
            usernames = json.dumps(self.__db.get_all_usernames())
            self.__send_message(Message(
                MessagePurpose.GET_ALL_USERNAMES,
                self.ip_addr,
                CommandData(usernames),
            ), encoding.decode_ip_addr(ip_addr))

        # get a user's IP address given their username
        elif mes.mes_purpose == MessagePurpose.GET_IP_ADDR:
            ip_addr = mes.sender
            username = mes.content.value.split("\0")[0]
            username_ip_addr = self.__db.get_ip_addr_from_username(username)
            self.__send_message(Message(
                MessagePurpose.GET_IP_ADDR,
                self.ip_addr,
                CommandData(username_ip_addr),
            ), encoding.decode_ip_addr(ip_addr))

    def run(self) -> None:
        self.is_running = True
        threading.Thread(
            target=self._listen_loop,
            args=(self.__handle_message,),
        ).start()
