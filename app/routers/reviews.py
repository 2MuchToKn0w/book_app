from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.depends import get_async_db
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel

from app.schemas.reviews import Review as ReviewSchema, ReviewUpdate
from app.auth import get_current_user


router = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)


@router.patch("/{review_id}", response_model=ReviewSchema)
async def patch_review(
    review_id: int,
    review: ReviewUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Update a review:
    - Owner can update their own review
    - Admin can update any review
    """

    review_db = await db.scalar(
        select(ReviewModel).where(ReviewModel.id == review_id)
    )

    if not review_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if review_db.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can edit only your own review",
        )

    update_data = review.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided for update",
        )

    for field, value in update_data.items():
        setattr(review_db, field, value)

    review_db.updated_at = datetime.now(timezone.utc)

    db.add(review_db)
    await db.commit()
    await db.refresh(review_db)

    return review_db


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a review:
    - Owner can delete their own review
    - Admin can delete any review
    """

    review_db = await db.scalar(
        select(ReviewModel).where(ReviewModel.id == review_id)
    )

    if not review_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if review_db.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can delete only your own review",
        )

    await db.delete(review_db)
    await db.commit()

    return None