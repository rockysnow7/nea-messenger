import socket
import threading
import time
import ip
import database

from message import Message, MessagePurpose, TextData
from constants import USERNAME_MAX_LEN
from rsa import rsa_encrypt, rsa_decrypt


SERVER_IP_ADDR = "192.168.0.35" # this machine

CLIENT_SEND_PORT = 8000
SERVER_SEND_PORT = 8001
CLIENT_RECV_PORT = 8002
SERVER_RECV_PORT = 8003


class Node:
    def __init__(self, is_client: bool) -> None:
        self.ip_addr = ip.get_host_ip_addr()
        self._is_running = False
        self._recvd_messages = []

        self.__recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__recv_socket.bind((self.ip_addr, CLIENT_RECV_PORT if is_client else SERVER_RECV_PORT))

    def _send_bytes_to_ip(self, ip_addr: str, data: bytes, recipient_is_client: bool) -> None:
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((ip_addr, CLIENT_RECV_PORT if recipient_is_client else SERVER_RECV_PORT))
        send_socket.sendall(data)
        send_socket.close()

    def _listen_loop(self) -> None:
        self.__recv_socket.listen()
        while self._is_running:
            conn, addr = self.__recv_socket.accept()
            with conn:
                print(f"Connected to {addr}.")
                while True:
                    data = conn.recv(1044)
                    if not data:
                        self._is_running = False
                        break

                    mes = Message.from_bytes(data)
                    self._recvd_messages.append(mes)

class Client(Node):
    def __init__(self) -> None:
        super().__init__(True)
        self.__rsa_priv_keys = {}

    def send_message(self, mes: Message, encrypt: bool = False) -> None:
        """
        Sends `mes` to the server to be handled.
        """

        if encrypt:
            mes = rsa_encrypt(mes)
        self._send_bytes_to_ip(SERVER_IP_ADDR, bytes(mes), False)

    def __handle_message(self, mes: Message) -> None:
        if mes.mes_purpose == MessagePurpose.EXCHANGE:
            self.__handle_key_exchange(mes)

    def __handle_key_exchange(self, mes: Message) -> None:
        """
        Handles the Diffie-Hellman key exchange.
        """

        ...

    def __handle_message_loop(self) -> None:
        while True:
            if self._recvd_messages:
                self.__handle_message(self._recvd_messages[0])
                del self._recvd_messages[0]

    def __send_loop(self) -> None:
        while self._is_running:
            data = input("data: ").encode("utf-8")
            self._send_bytes_to_ip(self.ip_addr, data, False)
            time.sleep(0.1)

    def run(self) -> None:
        self._is_running = True
        threading.Thread(target=self._listen_loop).start()
        threading.Thread(target=self.__handle_message_loop).start()
        threading.Thread(target=self.__send_loop).start()

class Server(Node):
    def __init__(self) -> None:
        super().__init__(False)

        self.__db = database.Database()

    def __send_message(self, mes: Message, recipient_ip: str) -> None:
        self._send_bytes_to_ip(recipient_ip, bytes(mes), True)

    def __handle_message(self, mes: Message) -> None:
        if mes.mes_purpose == MessagePurpose.MESSAGE:
            self.__db.save_message(mes)

        elif mes.mes_purpose == MessagePurpose.CREATE_USER:
            ip_addr = mes.sender
            username = mes.content.value[:USERNAME_MAX_LEN].split("\0")[0]
            password_hash = mes.content.value[database.USERNAME_MAX_LEN:database.USERNAME_MAX_LEN + 64]
            print(f"{username=}")
            print(f"{password_hash=}")

            if username not in self.__db.get_all_usernames():
                self.__db.create_new_user(username, ip_addr, password_hash)

    def __handle_message_loop(self) -> None:
        while True:
            if self._recvd_messages:
                print(f"{self._recvd_messages[0]=}")
                self.__handle_message(self._recvd_messages[0])
                del self._recvd_messages[0]

    def run(self) -> None:
        self._is_running = True
        threading.Thread(target=self._listen_loop).start()
        threading.Thread(target=self.__handle_message_loop).start()
