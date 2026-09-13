"""Internal admin APIs. Identity is the BFF JWT; role is loaded from SQLite."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.internal_users import UserView, _view
from app.core.internal_auth import require_admin
from app.db.sqlite import (
    LocalUser,
    list_users,
    set_plan,
    set_status,
    upsert_user,
    usage_summary,
    write_audit,
)

router = APIRouter()


class ProvisionBody(BaseModel):
    idp_user_id: str = Field(min_length=3, max_length=128)
    email_hash: str = Field(min_length=8, max_length=128)
    email_prefix: str = Field(default="", max_length=120)
    plan: str = Field(default="trial")


class PlanBody(BaseModel):
    plan: str
    daily_quota: int | None = Field(default=None, ge=0, le=10000)


@router.get("/internal/admin/users")
def admin_list_users(admin: Annotated[LocalUser, Depends(require_admin)]) -> list[UserView]:
    _ = admin
    return [_view(user) for user in list_users()]


@router.post("/internal/admin/users", response_model=UserView)
def admin_provision(
    body: ProvisionBody,
    admin: Annotated[LocalUser, Depends(require_admin)],
) -> UserView:
    if body.plan not in {"trial", "user"}:
        raise HTTPException(status_code=400, detail={"error": "invalid_plan"})
    user = upsert_user(
        idp_user_id=body.idp_user_id,
        email_hash=body.email_hash,
        email_prefix=body.email_prefix,
        plan=body.plan,
        role="user",
    )
    write_audit(action="provision", actor_user_id=admin.idp_user_id)
    return _view(user)


@router.post("/internal/admin/users/{idp_id}/revoke", response_model=UserView)
def admin_revoke(
    idp_id: str,
    admin: Annotated[LocalUser, Depends(require_admin)],
) -> UserView:
    user = set_status(idp_user_id=idp_id, status="revoked")
    if user is None:
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    write_audit(action="revoke", actor_user_id=admin.idp_user_id)
    return _view(user)


@router.post("/internal/admin/users/{idp_id}/plan", response_model=UserView)
def admin_plan(
    idp_id: str,
    body: PlanBody,
    admin: Annotated[LocalUser, Depends(require_admin)],
) -> UserView:
    try:
        user = set_plan(
            idp_user_id=idp_id, plan=body.plan, daily_quota=body.daily_quota
        )
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "invalid_plan"}) from None
    if user is None:
        raise HTTPException(status_code=404, detail={"error": "not_found"})
    write_audit(action="plan_change", actor_user_id=admin.idp_user_id)
    return _view(user)


@router.get("/internal/admin/usage")
def admin_usage(admin: Annotated[LocalUser, Depends(require_admin)]) -> dict:
    _ = admin
    return usage_summary()
