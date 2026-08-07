import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_access_token
from app.domain.enums import UserRole
from app.models.entities import User

bearer = HTTPBearer(auto_error=False)
Db = Annotated[AsyncSession, Depends(get_db)]


async def current_user(
    db: Db, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
) -> User:
    if not credentials:
        raise HTTPException(401, "Authentication required")
    try:
        payload = decode_access_token(credentials.credentials)
        user = await db.get(User, uuid.UUID(payload["sub"]))
    except (jwt.InvalidTokenError, ValueError, KeyError) as exc:
        raise HTTPException(401, "Invalid or expired access token") from exc
    if not user or not user.is_active:
        raise HTTPException(401, "Account unavailable")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def staff(user: CurrentUser) -> User:
    if user.role not in {UserRole.agent, UserRole.administrator}:
        raise HTTPException(403, "Staff access required")
    return user


StaffUser = Annotated[User, Depends(staff)]


def administrator(user: CurrentUser) -> User:
    if user.role != UserRole.administrator:
        raise HTTPException(403, "Administrator access required")
    return user


AdministratorUser = Annotated[User, Depends(administrator)]
