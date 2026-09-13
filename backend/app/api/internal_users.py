"""Internal BFF user sync. Not a public /chat contract."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.internal_auth import JwtClaims, get_auth_user, require_jwt
from app.core.quota import seconds_until_utc_midnight
from app.db.sqlite import LocalUser, get_user_by_idp, used_today, write_audit

router = APIRouter()


class EnsureRequest(BaseModel):
    email_prefix: str = Field(default="", max_length=120)


class UserView(BaseModel):
    id: str
    idp_user_id: str
    role: str
    plan: str
    status: str
    daily_quota: int | None
    quota: int
    used_today: int
    retry_after_seconds: int
    email_prefix: str
    must_reset_password: bool = False


def _view(user: LocalUser) -> UserView:
    settings = get_settings()
    quota = user.effective_daily_quota(
        settings.chat_daily_limit_trial, settings.chat_daily_limit_user
    )
    return UserView(
        id=user.id,
        idp_user_id=user.idp_user_id,
        role=user.role,
        plan=user.plan,
        status=user.status,
        daily_quota=user.daily_quota,
        quota=quota,
        used_today=used_today(user.id),
        retry_after_seconds=seconds_until_utc_midnight(),
        email_prefix=user.email_prefix,
        must_reset_password=user.must_reset_password,
    )


@router.post("/internal/users/ensure", response_model=UserView)
def ensure_user(
    body: EnsureRequest,
    claims: Annotated[JwtClaims, Depends(require_jwt)],
) -> UserView:
    user = get_user_by_idp(claims.sub)
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    write_audit(action="ensure", actor_user_id=user.idp_user_id)
    _ = body
    return _view(user)


@router.get("/internal/users/me", response_model=UserView)
def me(user: Annotated[LocalUser | None, Depends(get_auth_user)] = None) -> UserView:
    if user is None:
        raise HTTPException(status_code=401, detail={"error": "unauthorized"})
    return _view(user)
