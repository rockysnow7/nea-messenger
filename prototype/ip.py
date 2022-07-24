import socket


def get_host_ip_addr() -> str:
    return socket.gethostbyname_ex(socket.gethostname())[-1][-1]
