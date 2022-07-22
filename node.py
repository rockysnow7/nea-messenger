from message import Message, MessagePurpose
from rsa import rsa_encrypt, rsa_decrypt


class Node:
    ...

class Client(Node):
    def __init__(self, server: Node):
        self.server = server
        self.rsa_priv_keys = {}

    def send_message(self, mes: Message):
        """
        Sends `mes` to the server to be handled.
        """

        mes_encrypted = rsa_encrypt(mes)
        self.server.receive_message(mes_encrypted)

    def receive_message(self, mes: Message):
        mes_decrypted = rsa_decrypt(mes)
        self.handle_message(mes_decrypted)

    def handle_message(self, mes: Message):
        if mes.mes_purpose == MessagePurpose.EXCHANGE:
            self.handle_key_exchange(mes)

    def handle_key_exchange(self, mes: Message):
        """
        Handles the Diffie-Hellman key exchange.
        """

        ...

    #def create_individual_chat(self, username: str):
    #    mes = Message(MessageType.COMMAND, "server", 

class Server(Node):
    def send_message(self, mes: Message, recipient: Node):
        recipient.receive_message(mes)

    def receive_message(self, mes: Message):
        self.handle_message(mes)
