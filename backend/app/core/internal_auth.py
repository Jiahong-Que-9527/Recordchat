"""Internal HMAC JWT between the Next.js BFF and FastAPI."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException

from app.core.config import get_settings
from app.db.sqlite import LocalUser, get_user_by_idp

ISS = "recordchat-bff"
AUD = "recordchat-backend"


class JwtClaims(dict[str, Any]):
    @property
    def sub(self) -> str:
        return str(self.get("sub") or "")

    @property
    def email_hash(self) -> str:
        return str(self.get("email_hash") or "")


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    pad = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + pad)


def sign_internal_jwt(
    *,
    sub: str,
    email_hash: str = "",
    secret: str | None = None,
    ttl_seconds: int | None = None,
) -> str:
    settings = get_settings()
    secret = secret if secret is not None else settings.internal_auth_secret
    ttl = ttl_seconds if ttl_seconds is not None else settings.internal_jwt_ttl_seconds
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "iss": ISS,
        "aud": AUD,
        "sub": sub,
        "email_hash": email_hash,
        "iat": now,
        "exp": now + ttl,
        "jti": str(uuid.uuid4()),
    }
    signing_input = (
        f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}."
        f"{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    )
    signature = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def verify_internal_jwt(token: str, *, leeway: int = 30) -> JwtClaims:
    settings = get_settings()
    secret = settings.internal_auth_secret
    if len(secret) < 32:
        raise HTTPException(status_code=503, detail={"error": "unavailable"})
    parts = token.split(".")
    if len(parts) != 3:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    signing_input = f"{parts[0]}.{parts[1]}"
    expected = hmac.new(
        secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    try:
        given = _b64url_decode(parts[2])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail={"error": "unauthorized"}) from exc
    if not hmac.compare_digest(expected, given):
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    try:
        payload = json.loads(_b64url_decode(parts[1]))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail={"error": "unauthorized"}) from exc
    if payload.get("iss") != ISS or payload.get("aud") != AUD:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    now = int(time.time())
    exp = int(payload.get("exp") or 0)
    if exp + leeway < now:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    return JwtClaims(payload)


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    prefix = "bearer "
    if authorization.lower().startswith(prefix):
        return authorization[len(prefix) :].strip()
    return None


def get_auth_user(
    authorization: Annotated[str | None, Header()] = None,
) -> LocalUser | None:
    """None when AUTH_MODE=off. 401 when enforced and JWT/user is invalid."""
    settings = get_settings()
    if not settings.auth_enforced():
        return None
    if len(settings.internal_auth_secret) < 32:
        raise HTTPException(status_code=503, detail={"error": "unavailable"})
    token = _bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    claims = verify_internal_jwt(token)
    user = get_user_by_idp(claims.sub)
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    if user.status == "revoked":
        raise HTTPException(status_code=401, detail={"error": "revoked"})
    return user


def require_jwt(
    authorization: Annotated[str | None, Header()] = None,
) -> JwtClaims:
    settings = get_settings()
    if len(settings.internal_auth_secret) < 32:
        raise HTTPException(status_code=503, detail={"error": "unavailable"})
    token = _bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    return verify_internal_jwt(token)
