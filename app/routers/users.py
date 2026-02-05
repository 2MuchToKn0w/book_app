from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User as UserModel
from app.schemas.users import User as UserSchema, UserCreate
from app.depends import get_async_db
from app.auth import hash_password


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
        user: UserCreate,
        db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new user
    """

    result = await db.scalar(select(UserModel).where(UserModel.email == user.email))
    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    db_user = UserModel(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password),
        role="user",
        is_active=True,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user