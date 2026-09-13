"""Internal admin APIs. Identity is the BFF JWT; role is loaded from SQLite."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.internal_users import UserView, _view
from app.core.internal_auth import require_admin
from app.api.auth import ProvisionEmailBody, ProvisionResult, provision_with_temp_password
from app.db.sqlite import (
    LocalUser,
    list_users,
    set_plan,
    set_status,
    usage_summary,
    write_audit,
)

router = APIRouter()


class PlanBody(BaseModel):
    plan: str
    daily_quota: int | None = Field(default=None, ge=0, le=10000)


@router.get("/internal/admin/users")
def admin_list_users(admin: Annotated[LocalUser, Depends(require_admin)]) -> list[UserView]:
    _ = admin
    return [_view(user) for user in list_users()]


@router.post("/internal/admin/users", response_model=ProvisionResult)
def admin_provision(
    body: ProvisionEmailBody,
    admin: Annotated[LocalUser, Depends(require_admin)],
) -> ProvisionResult:
    return provision_with_temp_password(email=body.email, plan=body.plan, admin=admin)


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
