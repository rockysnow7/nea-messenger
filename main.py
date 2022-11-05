#import encoding
#import ip

#from node import Server, Client
#from chat_type import ChatType
#from message import Message, MessagePurpose, TextData
#from rsa import gen_rsa_keys, rsa_encrypt, rsa_decrypt
#from sympy import prime

from node import Server
from ui import UI


server = Server()
print("server made")

ui = UI(server)
ui.main_loop()

#server.db.create_new_user(
#    "finn",
#    ip.get_host_ip_addr(),
#    encoding.hash_str("password"),
#)
#server.db.create_new_user(
#    "other",
#    ip.get_host_ip_addr(),
#    encoding.hash_str("1234"),
#)
#server.db.create_new_chat(
#    "finn_other",
#    ChatType.INDIVIDUAL,
#    1234,
#    ["finn", "other"],
#    ["finn", "other"],
#)
