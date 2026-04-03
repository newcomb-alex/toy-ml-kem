# src/mlkem.py
from __future__ import annotations
import hashlib
import hmac
import os
from typing import Dict, Tuple

from params import N
from kpke import kpke_keygen, kpke_encrypt, kpke_decrypt

MSG_BYTES = (N + 7) // 8
SHARED_KEY_BYTES = 32


# -----------------------------
# Hash/KDF helpers
# -----------------------------

def _H(data: bytes) -> bytes:
    """Hash helper: 32-byte digest."""
    return hashlib.sha3_256(data).digest()


def _J(data: bytes) -> bytes:
    """KDF helper: 32-byte shared-key output."""
    return hashlib.sha3_256(data).digest()


def _G(data: bytes) -> Tuple[bytes, bytes]:
    """
    Expand input into (Kbar, r), each 32 bytes.
    """
    out = hashlib.shake_256(data).digest(64)
    return out[:32], out[32:]


def _encode_ek_for_hash(ek: Dict) -> bytes:
    """
    Deterministic byte encoding of ek for hashing.

    ek = {"rho": bytes(32), "t": List[List[int]]}
    We encode:
      rho || all t coefficients as 2-byte little-endian integers.
    """
    rho = ek["rho"]
    t = ek["t"]

    out = bytearray(rho)
    for poly in t:
        for coeff in poly:
            out += int(coeff).to_bytes(2, "little", signed=False)
    return bytes(out)


# -----------------------------
# Internal API
# -----------------------------

def mlkem_keygen_internal(d: bytes, z: bytes) -> Tuple[Dict, Dict]:
    """
    Deterministic-ish internal key generation:
      - d seeds K-PKE keygen
      - z is fallback secret used in decapsulation failure branch

    Returns:
      ek: encapsulation key (public)
      dk: decapsulation key (secret, includes ek, H(ek), z)
    """
    ek_pke, dk_pke = kpke_keygen(d)
    h_ek = _H(_encode_ek_for_hash(ek_pke))

    ek = ek_pke
    dk = {
        "dk_pke": dk_pke,  # contains s
        "ek": ek_pke,
        "h_ek": h_ek,
        "z": z,
    }
    return ek, dk


def mlkem_encaps_internal(ek: Dict, m: bytes) -> Tuple[bytes, bytes]:
    """
    Internal encapsulation with caller-provided message seed m.

    Steps:
      Kbar, r = G(m || H(ek))
      c       = K-PKE.Encrypt(ek, m, r)
      K       = J(Kbar || H(c))
    """
    m = (m + b"\x00" * MSG_BYTES)[:MSG_BYTES]
    h_ek = _H(_encode_ek_for_hash(ek))

    Kbar, r = _G(m + h_ek)
    c = kpke_encrypt(ek, m, r)
    K = _J(Kbar + _H(c))
    return c, K


def mlkem_decaps_internal(dk: Dict, c: bytes) -> bytes:
    """
    Internal decapsulation.

    Steps:
      m'          = K-PKE.Decrypt(dk_pke, c)
      Kbar', r'   = G(m' || h_ek)
      c'          = K-PKE.Encrypt(ek, m', r')
      if c == c': K = J(Kbar' || H(c))
      else:       K = J(z || H(c))
    """
    dk_pke = dk["dk_pke"]
    ek = dk["ek"]
    h_ek = dk["h_ek"]
    z = dk["z"]

    m_prime = kpke_decrypt(dk_pke, c)
    Kbar_prime, r_prime = _G(m_prime + h_ek)
    c_prime = kpke_encrypt(ek, m_prime, r_prime)

    hc = _H(c)
    if hmac.compare_digest(c, c_prime):
        return _J(Kbar_prime + hc)
    else:
        return _J(z + hc)


# -----------------------------
# Public API
# -----------------------------

def mlkem_keygen() -> Tuple[Dict, Dict]:
    """
    Public key generation with fresh randomness.
    """
    d = os.urandom(32)
    z = os.urandom(32)
    return mlkem_keygen_internal(d, z)


def mlkem_encaps(ek: Dict) -> Tuple[bytes, bytes]:
    """
    Public encapsulation with fresh randomness.
    Returns (ciphertext, shared_key).
    """
    m = os.urandom(MSG_BYTES)
    return mlkem_encaps_internal(ek, m)


def mlkem_decaps(dk: Dict, c: bytes) -> bytes:
    """
    Public decapsulation.
    Returns shared_key.
    """
    return mlkem_decaps_internal(dk, c)