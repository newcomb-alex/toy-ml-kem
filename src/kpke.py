# src/kpke.py

from __future__ import annotations
import hashlib
import os
from typing import Dict, List, Tuple

from params import (
    N, Q, K, ETA1, ETA2, DU, DV,
    ENCODED_POLY_DU_BYTES, ENCODED_POLY_DV_BYTES
)
from poly import poly_add, poly_sub, poly_mul_mod
from sampling import sample_cbd
from encoding import (
    compress_d, decompress_d,
    byte_encode_d, byte_decode_d,
    bytes_to_bits, bits_to_bytes
)

CIPHERTEXT_BYTES = K * ENCODED_POLY_DU_BYTES + ENCODED_POLY_DV_BYTES
MSG_BYTES = (N + 7) // 8


# -----------------------------
# Internal deterministic helpers
# -----------------------------

def _prf(seed: bytes, nonce: int, out_len: int, domain: bytes = b"") -> bytes:
    """
    Deterministic PRF-like byte expansion using SHAKE256.
    """
    return hashlib.shake_256(domain + seed + bytes([nonce & 0xFF])).digest(out_len)


def _sample_uniform_poly(seed: bytes, i: int, j: int, n: int = N, q: int = Q) -> List[int]:
    """
    Deterministically sample polynomial with coefficients in [0, q-1].
    Uses simple rejection sampling from SHAKE128 output bytes.
    """
    out: List[int] = []
    cutoff = (256 // q) * q  # accept bytes < cutoff, then mod q

    counter = 0
    while len(out) < n:
        buf = hashlib.shake_128(seed + bytes([i & 0xFF, j & 0xFF, counter & 0xFF])).digest(64)
        for b in buf:
            if b < cutoff:
                out.append(b % q)
                if len(out) == n:
                    break
        counter += 1

    return out


def _expand_a(rho: bytes, k: int = K) -> List[List[List[int]]]:
    """
    Expand k x k matrix A of polynomials from seed rho.
    A[i][j] is a polynomial in R_q.
    """
    return [[_sample_uniform_poly(rho, i, j, N, Q) for j in range(k)] for i in range(k)]


def _sample_noise_poly(sigma: bytes, nonce: int, eta: int) -> List[int]:
    """
    Sample one CBD polynomial using seed sigma and nonce.
    """
    def prng_bytes(num_bytes: int) -> bytes:
        return _prf(sigma, nonce, num_bytes, domain=b"CBD")
    return sample_cbd(eta=eta, n=N, prng_bytes=prng_bytes, q=Q)


def _mat_vec_mul(A: List[List[List[int]]], s: List[List[int]]) -> List[List[int]]:
    """
    Matrix-vector multiplication over R_q:
    out[i] = sum_j A[i][j] * s[j]
    """
    out: List[List[int]] = []
    for i in range(K):
        acc = [0] * N
        for j in range(K):
            prod = poly_mul_mod(A[i][j], s[j], Q, N)
            acc = poly_add(acc, prod, Q)
        out.append(acc)
    return out


def _matT_vec_mul(A: List[List[List[int]]], y: List[List[int]]) -> List[List[int]]:
    """
    Multiply transpose(A) by vector y:
    out[i] = sum_j A[j][i] * y[j]
    """
    out: List[List[int]] = []
    for i in range(K):
        acc = [0] * N
        for j in range(K):
            prod = poly_mul_mod(A[j][i], y[j], Q, N)
            acc = poly_add(acc, prod, Q)
        out.append(acc)
    return out


def _vec_dot(a: List[List[int]], b: List[List[int]]) -> List[int]:
    """
    Dot product of polynomial vectors over R_q:
    sum_i a[i] * b[i]
    """
    acc = [0] * N
    for i in range(K):
        prod = poly_mul_mod(a[i], b[i], Q, N)
        acc = poly_add(acc, prod, Q)
    return acc


def _msg_to_poly(m: bytes) -> List[int]:
    """
    Map N message bits to a polynomial:
    bit 0 -> 0
    bit 1 -> floor((Q+1)/2)
    """
    bits = bytes_to_bits(m)
    if len(bits) < N:
        bits = bits + [0] * (N - len(bits))
    bits = bits[:N]
    half = (Q + 1) // 2
    return [(bit * half) % Q for bit in bits]


def _poly_to_msg(p: List[int]) -> bytes:
    """
    Recover N message bits via 1-bit compression:
    bit_i = Compress_1(p[i])
    """
    bits = [compress_d(x % Q, Q, 1) for x in p[:N]]
    return bits_to_bytes(bits[:N])


# -----------------------------
# Public Functions
# -----------------------------

def kpke_keygen(seed: bytes | None = None) -> Tuple[Dict, Dict]:
    """
    K-PKE.KeyGen

    Returns:
      ek: {"rho": bytes, "t": List[List[int]]}
      dk: {"s": List[List[int]]}
    """
    if seed is None:
        seed = os.urandom(32)

    # Derive rho (matrix seed) and sigma (noise seed)
    d = hashlib.shake_256(seed).digest(64)
    rho, sigma = d[:32], d[32:]

    A = _expand_a(rho, K)

    # Sample secret and error vectors
    s: List[List[int]] = []
    e: List[List[int]] = []
    nonce = 0
    for _ in range(K):
        s.append(_sample_noise_poly(sigma, nonce, ETA1))
        nonce += 1
    for _ in range(K):
        e.append(_sample_noise_poly(sigma, nonce, ETA1))
        nonce += 1

    # t = A*s + e
    As = _mat_vec_mul(A, s)
    t = [poly_add(As[i], e[i], Q) for i in range(K)]

    ek = {"rho": rho, "t": t}
    dk = {"s": s}
    return ek, dk


def kpke_encrypt(ek: Dict, m: bytes, coins: bytes | None = None) -> bytes:
    """
    K-PKE.Encrypt

    Inputs:
      ek: public key dict from kpke_keygen
      m : message bytes (uses first N bits)
      coins: optional deterministic randomness seed

    Output:
      ciphertext bytes c = Encode(u_compressed_vector) || Encode(v_compressed_poly)
    """
    rho: bytes = ek["rho"]
    t: List[List[int]] = ek["t"]

    if coins is None:
        coins = os.urandom(32)

    # Expand A from rho
    A = _expand_a(rho, K)

    # Sample y (eta1), e1 vector (eta2), e2 poly (eta2)
    y: List[List[int]] = []
    e1: List[List[int]] = []
    nonce = 0
    for _ in range(K):
        y.append(_sample_noise_poly(coins, nonce, ETA1))
        nonce += 1
    for _ in range(K):
        e1.append(_sample_noise_poly(coins, nonce, ETA2))
        nonce += 1
    e2 = _sample_noise_poly(coins, nonce, ETA2)

    mu = _msg_to_poly(m)

    # u = A^T * y + e1
    u = _matT_vec_mul(A, y)
    u = [poly_add(u[i], e1[i], Q) for i in range(K)]

    # v = t^T * y + e2 + mu
    v = _vec_dot(t, y)
    v = poly_add(v, e2, Q)
    v = poly_add(v, mu, Q)

    # Compress + encode ciphertext
    c = bytearray()

    for i in range(K):
        u_comp = [compress_d(x % Q, Q, DU) for x in u[i]]
        c += byte_encode_d(u_comp, DU, N)

    v_comp = [compress_d(x % Q, Q, DV) for x in v]
    c += byte_encode_d(v_comp, DV, N)

    return bytes(c)


def kpke_decrypt(dk: Dict, c: bytes) -> bytes:
    """
    K-PKE.Decrypt

    Input:
      dk: secret key dict from kpke_keygen
      c : ciphertext bytes from kpke_encrypt

    Output:
      recovered message bytes (first N bits meaningful)
    """
    if len(c) != CIPHERTEXT_BYTES:
        raise ValueError(f"Invalid ciphertext length: got {len(c)}, expected {CIPHERTEXT_BYTES}")

    s: List[List[int]] = dk["s"]

    # Decode + decompress u vector
    u: List[List[int]] = []
    off = 0
    for _ in range(K):
        chunk = c[off:off + ENCODED_POLY_DU_BYTES]
        off += ENCODED_POLY_DU_BYTES

        u_comp = byte_decode_d(chunk, DU, N, 1 << DU)
        u_poly = [decompress_d(x, Q, DU) % Q for x in u_comp]
        u.append(u_poly)

    # Decode + decompress v polynomial
    v_chunk = c[off:off + ENCODED_POLY_DV_BYTES]
    v_comp = byte_decode_d(v_chunk, DV, N, 1 << DV)
    v = [decompress_d(x, Q, DV) % Q for x in v_comp]

    # m' from v - s^T*u
    su = _vec_dot(s, u)
    w = poly_sub(v, su, Q)

    return _poly_to_msg(w)