# src/sampling.py
from typing import List, Callable
from encoding import bytes_to_bits

def sample_cbd(eta: int, n: int, prng_bytes: Callable[[int], bytes], q: int) -> List[int]:
    """
    Sample polynomial coefficients from centered binomial distribution D_eta.
    Uses 2*eta bits per coefficient.
    """
    total_bits = 2 * eta * n
    total_bytes = (total_bits + 7) // 8
    buf = prng_bytes(total_bytes)
    bits = bytes_to_bits(buf)

    coeffs = []
    for i in range(n):
        x = sum(bits[2 * eta * i + j] for j in range(eta))
        y = sum(bits[2 * eta * i + eta + j] for j in range(eta))
        coeffs.append((x - y) % q)
    return coeffs