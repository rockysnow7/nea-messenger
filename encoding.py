from hashlib import sha256


def encode_ip_addr(ip_addr: str) -> str:
    """
    Returns an IPv4 address as a hex string.

    :param ip_addr: the IPv4 address, of the form n.n.n.n, where each n is an
    8-bit int
    :returns: an 8 digit hex string representing `ip_addr`
    """

    ns = [int(i) for i in ip_addr.split(".")]
    ns_hex = [hex(i)[2:].zfill(2) for i in ns]

    return "".join(ns_hex)

def decode_ip_addr(ip_addr_hex: str) -> str:
    """
    Returns an IPv4 address given its hex representation (as returned by
    `ip_addr_as_hex`).

    :param ip_addr_hex: the 8 digit hex string representing an IPv4 address
    :returns: the original IPv4 address
    """

    ns_hex = [ip_addr_hex[i:i+2] for i in range(0, 8, 2)]
    ns = [int(i, 16) for i in ns_hex]

    return ".".join(str(i) for i in ns)


def hash_str(s: str) -> str:
    """
    SHA-256 hash a given string.

    :param s: the string to be hashed
    :returns: the SHA-256 hash of `s`
    """

    return sha256(s.encode("utf-8")).hexdigest()

def zfill_bytes(s: bytes, n: int) -> bytes:
    return bytes(n - len(s)) + s

def zremove_bytes(s: bytes) -> bytes:
    return s.split(b"\0")[-1]
