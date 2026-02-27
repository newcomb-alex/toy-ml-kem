# src/poly.py
from typing import List

def mod_q(x: int, q: int) -> int:
    return x % q

def poly_add(a: List[int], b: List[int], q: int) -> List[int]:
    return [(x + y) % q for x, y in zip(a, b)]

def poly_sub(a: List[int], b: List[int], q: int) -> List[int]:
    return [(x - y) % q for x, y in zip(a, b)]

def poly_mul_mod(a: List[int], b: List[int], q: int, n: int) -> List[int]:
    """
    Multiply in R_q = Z_q[X]/(X^n + 1) using naive convolution.
    Rule: X^n = -1, so terms wrap with a sign flip.
    """
    res = [0] * n
    for i in range(n):
        for j in range(n):
            prod = a[i] * b[j]
            idx = i + j
            if idx < n:
                res[idx] += prod
            else:
                res[idx - n] -= prod
    return [x % q for x in res]