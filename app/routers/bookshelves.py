from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.depends import get_async_db
from app.models.bookshelves import BookShelf as BookShelfModel
from app.models.users import User as UserModel

from app.schemas.bookshelves import BookShelf as BookShelfSchema, BookShelfCreate
from app.auth import get_current_user


router = APIRouter(
    prefix="/bookshelves",
    tags=["bookshelves"],
)


@router.post("/", response_model=BookShelfSchema, status_code=status.HTTP_201_CREATED)
async def create_bookshelf(
        bookshelf_data: BookShelfCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new bookshelf for the current user
    """

    # Check if a list with the same name already exists for the user
    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.user_id == current_user.id,
            BookShelfModel.name == bookshelf_data.name,
        )
    )
    existing_bookshelf = result.scalars().first()


    if existing_bookshelf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a bookshelf with this name."
        )

    new_bookshelf = BookShelfModel(
        name=bookshelf_data.name,
        description=bookshelf_data.description,
        user_id=current_user.id,
    )

    db.add(new_bookshelf)
    await db.commit()
    await db.refresh(new_bookshelf)

    return new_bookshelf


@router.get("/", response_model=list[BookShelfSchema])
async def get_bookshelves(
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Get all bookshelves of the current user
    """

    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.user_id == current_user.id,
        )
    )

    bookshelves = result.scalars().all()

    return bookshelves