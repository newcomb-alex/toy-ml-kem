# src/encoding.py
from typing import List

def compress_d(x: int, q: int, d: int) -> int:
    two_d = 1 << d
    return ((x * two_d + q // 2) // q) % two_d

def decompress_d(y: int, q: int, d: int) -> int:
    two_d = 1 << d
    return (y * q + (two_d // 2)) // two_d

def bytes_to_bits(byte_arr: bytes) -> List[int]:
    bits = []
    for b in byte_arr:
        for i in range(8):
            bits.append((b >> i) & 1)
    return bits

def bits_to_bytes(bits: List[int]) -> bytes:
    out = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        out[i // 8] |= (bit & 1) << (i % 8)
    return bytes(out)

def byte_encode_d(F: List[int], d: int, n: int) -> bytes:
    """
    Kyber-like, but scaled: output length = (n * d) / 8 bytes.
    """
    bits = []
    for x in F:
        for j in range(d):
            bits.append((x >> j) & 1)
    return bits_to_bytes(bits)

def byte_decode_d(B: bytes, d: int, n: int, m: int) -> List[int]:
    """
    Decode bytes into n integers mod m, each d bits.
    """
    bits = bytes_to_bits(B)
    out = []
    for i in range(n):
        val = 0
        for j in range(d):
            val |= (bits[i * d + j] << j)
        out.append(val % m)
    return out