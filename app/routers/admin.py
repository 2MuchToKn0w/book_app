from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User as UserModel
from app.models.reviews import Review as ReviewModel
from app.schemas.admin import UserOut, UpdateUserRole, AdminReviewUpdate
from app.schemas.reviews import Review as ReviewsSchema
from app.depends import get_async_db
from app.auth import get_current_admin


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


#------------------------------#
# Endpoints for managing users #
#------------------------------#

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


#--------------------------------#
# Endpoints for managing reviews #
#--------------------------------#

@router.patch("/reviews/{review_id}", response_model=ReviewsSchema)
async def update_review(
        review_id: int,
        data: AdminReviewUpdate,
        admin: UserModel = Depends(get_current_admin),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Update the text of a user's review
    """

    result = await db.scalars(
        select(ReviewModel)
        .where(ReviewModel.id == review_id)
    )
    review = result.first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    if data.comment is not None:
        review.comment = data.comment

    db.add(review)
    await db.commit()
    await db.refresh(review)

    return review


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
        review_id: int,
        admin: UserModel = Depends(get_current_admin),
        db: AsyncSession = Depends(get_async_db),
):
    """
    Deletes a review by its ID
    """

    result = await db.scalars(
        select(ReviewModel)
        .where(ReviewModel.id == review_id)
    )
    review = result.first()

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )

    await db.delete(review)
    await db.commit()

    return None