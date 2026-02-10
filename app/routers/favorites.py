from fastapi import APIRouter, Request, Query, HTTPException, status, Depends
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.depends import get_async_db
from app.models.favorites import Favorite as FavoriteModel
from app.models.users import User as UserModel

from app.schemas.favorites import Favorite as FavoriteSchema, FavoriteList
from app.auth import get_current_user


router = APIRouter(
    prefix="/favorites",
    tags=["favorites"],
)


@router.get("/", response_model=FavoriteList)
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> FavoriteList:
    """
      Returns a paginated list of favorite books with detailed information
      """

    # Count total number of books for this user
    total = await db.scalar(
        select(func.count())
        .select_from(FavoriteModel)
        .where(FavoriteModel.user_id == current_user.id)
    )
    offset = (page - 1) * page_size

    result = await db.execute(
        select(FavoriteModel)
        .where(FavoriteModel.user_id == current_user.id)
        .limit(page_size)
        .offset(offset)
    )
    favorites = result.scalars().all()

    # Create response as a FavoriteList
    return FavoriteList(
        items=favorites,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{work_olid}", response_model=FavoriteSchema, status_code=status.HTTP_201_CREATED)
async def add_to_favorite(
    olid_id: str,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> FavoriteSchema:
    """
       Adds a book to the favorites list by its OLID
       Fetches book data from OpenLibraryService and saves it to the database
       Returns the created favorite book
       """

    # Fetch book data by olid_id via OpenLibraryService
    service = request.app.state.open_library_service
    results = await service.get_book_by_work(olid_id)

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This book not found",
        )

    # Check if the book is already in favorites
    exists = await db.scalar(
        select(FavoriteModel).where(
            FavoriteModel.work_olid == olid_id,
            FavoriteModel.user_id == current_user.id
        )
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This book already exists",
        )

    favorite = FavoriteModel(
        work_olid=olid_id,
        title=results.get("title"),
        authors=", ".join(results.get("authors") or []),
        cover_url=results.get("cover_url"),
        year=results.get("year"),
        user_id=current_user.id,
    )

    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    return favorite


@router.delete("/{work_olid}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_favorite(
    olid_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Removes a book from the favorites list by its OLID
    """

    # Check if the book exists in the current user's favorites
    favorite = await db.scalar(
        select(FavoriteModel)
        .where(FavoriteModel.work_olid == olid_id,
               FavoriteModel.user_id == current_user.id)
    )

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This book is not in favorites",
        )

    # Remove the book from favorites only for the current user
    await db.execute(
        delete(FavoriteModel)
        .where(
            FavoriteModel.work_olid == olid_id,
            FavoriteModel.user_id == current_user.id
        )
    )

    await db.commit()

    return None