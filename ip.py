import socket


def get_host_ip_addr() -> str:
    """
    Returns the IP address of the host machine.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_addr = s.getsockname()[0]
    s.close()

    return ip_addr
