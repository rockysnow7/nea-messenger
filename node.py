import socket
import threading
import time
import ip
import database

from message import Message, MessagePurpose, TextData
from rsa import rsa_encrypt, rsa_decrypt


SERVER_IP_ADDR = "192.168.0.35" # this machine

SEND_PORT = 8000
RECV_PORT = 8001


class Node:
    def __init__(self) -> None:
        self.ip_addr = ip.get_host_ip_addr()
        print(f"{self.ip_addr=}")
        self.__is_running = False

        self.__recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__recv_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__recv_socket.bind((self.ip_addr, RECV_PORT))

    def _send_bytes_to_ip(self, ip_addr: str, data: bytes) -> None:
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        send_socket.connect((ip_addr, RECV_PORT))
        send_socket.sendall(data)
        send_socket.close()

    def __listen_loop(self) -> None:
        self.__recv_socket.listen()
        break_flag = False
        while self.__is_running:
            conn, addr = self.__recv_socket.accept()
            with conn:
                print(f"Connected to {addr}.")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        self.__is_running = False
                        break
                    print(f"{data=}")

    def __send_loop(self) -> None:
        while self.__is_running:
            data = input("data: ").encode("utf-8")
            self._send_bytes_to_ip(self.ip_addr, data)
            time.sleep(0.1)

    def main_loop(self) -> None:
        self.__is_running = True
        threading.Thread(target=self.__listen_loop).start()
        threading.Thread(target=self.__send_loop).start()

class Client(Node):
    def __init__(self, server: Node) -> None:
        super().__init__()

        self.__server = server
        self.__rsa_priv_keys = {}

    def send_message(self, mes: Message, encrypt: bool = False) -> None:
        """
        Sends `mes` to the server to be handled.
        """

        if encrypt:
            mes = rsa_encrypt(mes)
        self.__server.receive_message(mes)

    def receive_message(self, mes: Message) -> None:
        mes_decrypted = rsa_decrypt(mes)
        self.__handle_message(mes_decrypted)

    def __handle_message(self, mes: Message) -> None:
        if mes.mes_purpose == MessagePurpose.EXCHANGE:
            self.__handle_key_exchange(mes)

    def __handle_key_exchange(self, mes: Message) -> None:
        """
        Handles the Diffie-Hellman key exchange.
        """

        ...

class Server(Node):
    def __init__(self) -> None:
        super().__init__()

        self.__db = database.Database()

    def __send_message(self, mes: Message, recipient: Node) -> None:
        recipient.receive_message(mes)

    def receive_message(self, mes: Message) -> None:
        self.__handle_message(mes)

    def __handle_message(self, mes: Message) -> None:
        if mes.mes_purpose == MessagePurpose.MESSAGE:
            self.__db.save_message(mes)

        elif mes.mes_purpose == MessagePurpose.CREATE_USER:
            ip_addr = mes.sender
            username = mes.content.value[:database.USERNAME_MAX_LEN].split("\0")[0]
            password_hash = mes.content.value[database.USERNAME_MAX_LEN:database.USERNAME_MAX_LEN + 64]
            print(f"{ip_addr=}")
            print(f"{username=}")
            print(f"{password_hash=}")

            if username not in self._db.get_all_usernames():
                print(f"{self.__db.get_all_usernames()=}")
                self.__db.create_new_user(username, ip_addr, password_hash)
