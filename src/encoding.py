# src/encoding.py
from typing import List

def compress_d(x: int, q: int, d: int) -> int:
    """
    Stores polynomial coefficients using fewer bits.
    """
    two_d = 1 << d
    return ((x * two_d + q // 2) // q) % two_d

def decompress_d(y: int, q: int, d: int) -> int:
    """
    Takes the d-bit compressed value and converts it back into its original full
    value.
    """
    two_d = 1 << d
    return (y * q + (two_d // 2)) // two_d

def bytes_to_bits(byte_arr: bytes) -> List[int]:
    """
    Converts an array of bytes into an array of bits.
    """
    bits = []
    for b in byte_arr:
        for i in range(8):
            bits.append((b >> i) & 1)
    return bits

def bits_to_bytes(bits: List[int]) -> bytes:
    """
    Converts an array of bits into an array of bytes.
    """
    out = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        out[i // 8] |= (bit & 1) << (i % 8)
    return bytes(out)

def byte_encode_d(F: List[int], d: int, n: int) -> bytes:
    """
    Converts an array of integers modulo m into an array of bytes.
    """
    bits = []
    for x in F:
        for j in range(d):
            bits.append((x >> j) & 1)
    return bits_to_bytes(bits)

def byte_decode_d(B: bytes, d: int, n: int, m: int) -> List[int]:
    """
    Converts an array of bytes back into an array of integers modulo m.
    """
    bits = bytes_to_bits(B)
    out = []
    for i in range(n):
        val = 0
        for j in range(d):
            val |= (bits[i * d + j] << j)
        out.append(val % m)
    return out