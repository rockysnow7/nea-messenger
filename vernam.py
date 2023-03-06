import math


def int_to_str(n: int) -> str:
    n_bits = bin(n)[2:]
    n_bits = n_bits.zfill(len(n_bits) + len(n_bits) % 8)
    n_bytes = [n_bits[i:i+8] for i in range(0, len(n_bits), 8)]
    n_chars = [chr(int(b, 2)) for b in n_bytes]

    return "".join(n_chars)

def str_xor(a: str, b: str) -> str:
    c = ""
    for i in range(len(a)):
        c += chr(ord(a[i]) ^ ord(b[i]))

    return c

def crypt(s: str, key: int) -> str:
    key = int_to_str(key)
    key *= math.ceil(len(s) / len(key))

    result = str_xor(s, key)

    return result
