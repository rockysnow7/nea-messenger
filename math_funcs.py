import math


def lcm(a: int, b: int) -> int:
    return abs(a * b) // math.gcd(a, b)

def is_coprime(a: int, b: int) -> bool:
    return math.gcd(a, b) == 1

def mod_mul_inv(a: int, m: int) -> int:
    for i in range(1, m):
        if (a * i) % m == 1:
            return i
