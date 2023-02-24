import math
import itertools


def str_to_bits(s: str) -> list[int]:
    s_bytes = list(itertools.chain(bin(c)[2:].zfill(8) for c in bytes(s, encoding="utf-8")))
    s_bits = [int(i) for i in "".join(s_bytes)]

    return s_bits

def bits_to_str(bits: list[int]) -> str:
    ...

def int_to_bits(n: int) -> list[int]:
    return [int(i) for i in bin(n)[2:].zfill(8)]

def vernam_encrypt(s: str, key: int) -> str:
    s_bits = str_to_bits(s)
    key_bits = int_to_bits(key)
    key_bits_full = key_bits * math.ceil(len(s_bits) / len(key_bits))
    xor_bits = [s_bits[i] ^ key_bits_full[i] for i in range(len(s_bits))]
    xor_s = bits_to_str(xor_bits)

    return xor_s

def vernam_decrypt(s: str, key: int) -> str:
    ...
