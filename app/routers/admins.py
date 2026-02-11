from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User as UserModel
from app.schemas.admins import UserOut, UpdateUserRole
from app.depends import get_async_db
from app.auth import get_current_admin


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/users", response_model=list[UserOut])
async def get_users(
        admin: UserModel = Depends(get_current_admin),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Returns a list of all users
    """

    result = await db.scalars(
        select(UserModel)
    )
    users = result.all()

    return users


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(
        user_id: int,
        admin: UserModel = Depends(get_current_admin),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Returns a specific user by user_id
    """

    result = await db.scalars(
        select(UserModel)
        .where(UserModel.id == user_id)
    )
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(
        user_id: int,
        data: UpdateUserRole,
        admin: UserModel = Depends(get_current_admin),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Update role and/or active status of a user
    """

    result = await db.scalars(
        select(UserModel)
        .where(UserModel.id == user_id)
    )
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if data.role is not None:
        user.role = data.role

    if data.is_active is not None:
        user.is_active = data.is_active

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        user_id: int,
        admin: UserModel = Depends(get_current_admin),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Permanently delete a user and all their related data
    """

    result = await db.scalars(
        select(UserModel)
        .where(UserModel.id == user_id)
    )
    user = result.first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()

    return None