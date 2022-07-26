import socket


def get_host_ip_addr() -> str:
    """
    Returns the IP address of the host machine.
    """

    return socket.gethostbyname_ex(socket.gethostname())[-1][-1]
