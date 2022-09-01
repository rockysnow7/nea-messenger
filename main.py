from message import Message, MessagePurpose, TextData
from rsa import gen_rsa_keys, rsa_encrypt, rsa_decrypt
from sympy import prime
from node import Node, Server
from prototype.database import Database, ChatType


#server = Server()

mes = Message(MessagePurpose.MESSAGE, "from", "to", TextData("hello"))
print(mes)

pub_key, priv_key = gen_rsa_keys(prime(20), prime(21))

encrypted = rsa_encrypt(mes, pub_key)
print(encrypted)
decrypted = rsa_decrypt(encrypted, priv_key)
print(decrypted)
