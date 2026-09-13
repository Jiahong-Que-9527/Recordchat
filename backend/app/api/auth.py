"""Email/password auth used by the Next.js BFF. Not a public /chat contract."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException  # Header used for session token
from pydantic import BaseModel, Field

from app.api.internal_users import UserView, _view
from app.core.config import get_settings
from app.core.passwords import (
    hash_password,
    hash_token,
    new_session_token,
    random_temp_password,
    validate_password,
    verify_password,
)
from app.db.sqlite import (
    LocalUser,
    create_local_user,
    create_session,
    delete_session,
    get_user_by_email,
    get_user_by_session,
    record_login_failure,
    record_login_success,
    set_password,
    write_audit,
)

router = APIRouter()


class EmailPasswordBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class ChangePasswordBody(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=1, max_length=128)


class SessionBody(BaseModel):
    session_token: str = Field(min_length=8, max_length=256)


class SessionView(BaseModel):
    session_token: str
    user: UserView
    must_reset_password: bool


def _norm_email(email: str) -> str:
    return email.strip().lower()


def _email_hash(email: str) -> str:
    import hashlib

    settings = get_settings()
    pepper = settings.email_hash_pepper or settings.internal_auth_secret
    return hashlib.sha256(f"{email}{pepper}".encode("utf-8")).hexdigest()


def _email_prefix(email: str) -> str:
    at = email.find("@")
    if at <= 0:
        return "***"
    return f"{email[: min(2, at)]}***{email[at:]}"


def _admin_role_for(email: str, user_id: str) -> str:
    settings = get_settings()
    emails = {item.strip().lower() for item in settings.admin_emails.split(",") if item.strip()}
    ids = {item.strip() for item in settings.admin_idp_user_ids.split(",") if item.strip()}
    if email in emails or user_id in ids:
        return "admin"
    return "user"


def _expires_at() -> str:
    settings = get_settings()
    when = datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _issue_session(user: LocalUser) -> SessionView:
    token = new_session_token()
    create_session(user_id=user.id, token_hash=hash_token(token), expires_at=_expires_at())
    return SessionView(
        session_token=token,
        user=_view(user),
        must_reset_password=user.must_reset_password,
    )


@router.post("/internal/auth/signup", response_model=SessionView)
def signup(body: EmailPasswordBody) -> SessionView:
    email = _norm_email(body.email)
    if "@" not in email:
        raise HTTPException(status_code=400, detail={"error": "invalid_email"})
    err = validate_password(body.password)
    if err:
        raise HTTPException(status_code=400, detail={"error": err})
    if get_user_by_email(email) is not None:
        raise HTTPException(status_code=409, detail={"error": "email_taken"})
    user = create_local_user(
        email=email,
        email_hash=_email_hash(email),
        email_prefix=_email_prefix(email),
        password_hash=hash_password(body.password),
        plan="trial",
        role="user",
        email_verified=True,
        must_reset_password=False,
    )
    if _admin_role_for(email, user.id) == "admin":
        from app.db.sqlite import upsert_user

        user = upsert_user(
            idp_user_id=user.idp_user_id,
            email_hash=user.email_hash,
            email_prefix=user.email_prefix,
            role="admin",
        )
    write_audit(action="signup", actor_user_id=user.idp_user_id)
    return _issue_session(user)


@router.post("/internal/auth/login", response_model=SessionView)
def login(body: EmailPasswordBody) -> SessionView:
    email = _norm_email(body.email)
    user = get_user_by_email(email)
    if user is None or not user.password_hash:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    if user.status != "active":
        raise HTTPException(status_code=401, detail={"error": "revoked"})
    if user.locked_until and user.locked_until > datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    ):
        raise HTTPException(status_code=429, detail={"error": "rate_limited", "retry_after_seconds": 900})
    if not verify_password(body.password, user.password_hash):
        record_login_failure(user_id=user.id)
        write_audit(action="login_fail", actor_user_id=user.idp_user_id)
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    record_login_success(user_id=user.id)
    if _admin_role_for(email, user.id) == "admin" and user.role != "admin":
        from app.db.sqlite import upsert_user

        user = upsert_user(
            idp_user_id=user.idp_user_id,
            email_hash=user.email_hash,
            email_prefix=user.email_prefix,
            role="admin",
        )
    write_audit(action="login_ok", actor_user_id=user.idp_user_id)
    return _issue_session(user)


@router.post("/internal/auth/session", response_model=SessionView)
def lookup_session(body: SessionBody) -> SessionView:
    user = get_user_by_session(hash_token(body.session_token))
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    return SessionView(
        session_token=body.session_token,
        user=_view(user),
        must_reset_password=user.must_reset_password,
    )


@router.post("/internal/auth/logout")
def logout(x_session_token: Annotated[str | None, Header()] = None) -> dict:
    if x_session_token:
        delete_session(hash_token(x_session_token))
    return {"ok": True}


@router.post("/internal/auth/change-password", response_model=UserView)
def change_password(
    body: ChangePasswordBody,
    x_session_token: Annotated[str | None, Header()] = None,
) -> UserView:
    if not x_session_token:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    user = get_user_by_session(hash_token(x_session_token))
    if user is None or user.status != "active":
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    err = validate_password(body.new_password)
    if err:
        raise HTTPException(status_code=400, detail={"error": err})
    set_password(user_id=user.id, password_hash=hash_password(body.new_password), must_reset=False)
    write_audit(action="password_change", actor_user_id=user.idp_user_id)
    refreshed = get_user_by_email(user.email)
    assert refreshed is not None
    return _view(refreshed)


class ProvisionEmailBody(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    plan: str = Field(default="trial")


class ProvisionResult(BaseModel):
    user: UserView
    temporary_password: str


def provision_with_temp_password(*, email: str, plan: str, admin: LocalUser) -> ProvisionResult:
    email_n = _norm_email(email)
    if "@" not in email_n:
        raise HTTPException(status_code=400, detail={"error": "invalid_email"})
    if plan not in {"trial", "user"}:
        raise HTTPException(status_code=400, detail={"error": "invalid_plan"})
    if get_user_by_email(email_n) is not None:
        raise HTTPException(status_code=409, detail={"error": "email_taken"})
    temp = random_temp_password()
    user = create_local_user(
        email=email_n,
        email_hash=_email_hash(email_n),
        email_prefix=_email_prefix(email_n),
        password_hash=hash_password(temp),
        plan=plan,
        role="user",
        email_verified=True,
        must_reset_password=True,
    )
    write_audit(action="provision", actor_user_id=admin.idp_user_id)
    return ProvisionResult(user=_view(user), temporary_password=temp)



