import database
import encoding
import ip

from chat_type import ChatType
from message import Message, MessagePurpose, TextData
from rsa import gen_rsa_keys, rsa_encrypt, rsa_decrypt
from sympy import prime


db = database.Database()
db.create_new_user(
    "finn",
    ip.get_host_ip_addr(),
    encoding.hash_str("password"),
)
db.create_new_user(
    "other",
    ip.get_host_ip_addr(),
    encoding.hash_str("1234"),
)

db.create_new_chat(
    "finn_other",
    ChatType.INDIVIDUAL,
    1234,
    ["finn", "other"],
    ["finn", "other"],
)

db.save_message(Message(
    MessagePurpose.MESSAGE,
    "finn",
    "finn_other",
    "hey hey",
))
