"""Password hashing (stdlib scrypt) and session tokens."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
DKLEN = 32
MIN_PASSWORD_LEN = 10
MAX_PASSWORD_LEN = 128


def validate_password(password: str) -> str | None:
    if len(password) < MIN_PASSWORD_LEN:
        return "password_too_short"
    if len(password) > MAX_PASSWORD_LEN:
        return "password_too_long"
    if password.strip() != password or not password.strip():
        return "password_invalid"
    return None


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=DKLEN,
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        kind, n_s, r_s, p_s, salt_hex, hash_hex = stored.split("$")
        if kind != "scrypt":
            return False
        dk = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(n_s),
            r=int(r_s),
            p=int(p_s),
            dklen=DKLEN,
        )
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:  # noqa: BLE001
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def random_temp_password() -> str:
    return secrets.token_urlsafe(18)[:24]
