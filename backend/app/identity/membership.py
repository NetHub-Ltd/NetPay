"""Merchant membership — NetHubKe user id → NetPay merchant ACL."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.merchants import Merchant, MerchantMember

ALLOWED_ROLES = frozenset({"member", "admin"})


async def list_memberships_for_user(
    session: AsyncSession, user_id: UUID, *, include_deleted: bool = False
) -> list[MerchantMember]:
    stmt = select(MerchantMember).where(MerchantMember.user_id == user_id)
    if not include_deleted:
        stmt = stmt.where(MerchantMember.deleted_at == None)
    result = await session.exec(stmt)
    return list(result.all())


async def get_membership(
    session: AsyncSession, *, user_id: UUID, merchant_id: UUID
) -> MerchantMember | None:
    stmt = select(MerchantMember).where(
        MerchantMember.user_id == user_id,
        MerchantMember.merchant_id == merchant_id,
        MerchantMember.deleted_at == None
    )
    result = await session.exec(stmt)
    return result.first()


async def require_membership(
    session: AsyncSession, *, user_id: UUID, merchant_id: UUID
) -> MerchantMember:
    row = await get_membership(session, user_id=user_id, merchant_id=merchant_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="merchant_membership_required",
        )
    merchant = await session.get(Merchant, merchant_id)
    if merchant is None or merchant.status != "active" or merchant.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="merchant_inactive")
    return row


async def grant_membership(
    session: AsyncSession,
    *,
    user_id: UUID,
    merchant_id: UUID,
    role: str = "member",
) -> MerchantMember:
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_role")
    merchant = await session.get(Merchant, merchant_id)
    if merchant is None or merchant.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="merchant_not_found")

    existing = await session.exec(
        select(MerchantMember).where(
            MerchantMember.user_id == user_id,
            MerchantMember.merchant_id == merchant_id,
        )
    )
    row = existing.first()
    if row is not None:
        row.deleted_at = None
        row.role = role
        row.updated_at = datetime.now(UTC)
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    row = MerchantMember(user_id=user_id, merchant_id=merchant_id, role=role)
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def revoke_membership(
    session: AsyncSession, *, user_id: UUID, merchant_id: UUID
) -> None:
    row = await get_membership(session, user_id=user_id, merchant_id=merchant_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="membership_not_found")
    row.deleted_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    session.add(row)
    await session.commit()
