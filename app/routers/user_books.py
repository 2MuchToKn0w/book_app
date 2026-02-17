from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from datetime import datetime, UTC

from app.depends import get_async_db
from app.models.user_books import UserBook as UserBookModel
from app.models.users import User as UserModel
from app.models.books import Book as BookModel

from app.schemas.user_books import UserBook as UserBookSchema, UserBookAdd, ReadingStatus, UserBookUpdate
from app.auth import get_current_user
from app.services.open_library import OpenLibraryService


router = APIRouter(
    prefix="/user-books",
    tags=["user-books"],
)


@router.post("/", response_model=UserBookSchema, status_code=status.HTTP_201_CREATED, summary="Add a book to user's reading list")
async def add_user_book(
        book_data: UserBookAdd,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
    Add a book to the current user's personal reading list.

    - If the book does not exist locally, it will be fetched from OpenLibrary
    - Default status is `PLANNED`
    - Progress and rating can be set during creation
    """

    # Check if already in user's list
    existing = await db.scalar(
        select(UserBookModel).where(
            UserBookModel.user_id == current_user.id,
            UserBookModel.work_olid == book_data.work_olid
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book is already in your list"
        )

    # Check if book exists in local books table
    book = await db.scalar(
        select(BookModel).where(BookModel.work_olid == book_data.work_olid)
    )

    # If not — fetch from OpenLibrary and save
    if not book:
        async with httpx.AsyncClient(base_url="https://openlibrary.org") as client:
            service = OpenLibraryService(client)
            book_data_ol = await service.get_book_by_work(book_data.work_olid)

        if book_data_ol:
            book = BookModel(
                work_olid=book_data_ol["work_olid"],
                title=book_data_ol["title"],
                authors=", ".join(book_data_ol["authors"]) if book_data_ol["authors"] else None,
                cover_url=book_data_ol["cover_url"],
                published_year=book_data_ol["year"],
            )
            db.add(book)
            await db.commit()
            await db.refresh(book)

    user_book = UserBookModel(
        user_id=current_user.id,
        work_olid=book_data.work_olid,
        status=book_data.status,
        progress_percent=book_data.progress_percent,
        rating=book_data.rating
    )

    db.add(user_book)
    await db.commit()
    await db.refresh(user_book)

    return UserBookSchema(
        id=user_book.id,
        work_olid=user_book.work_olid,
        status=user_book.status.value,
        progress_percent=user_book.progress_percent,
        rating=user_book.rating,
        started_at=user_book.started_at,
        finished_at=user_book.finished_at,
        created_at=user_book.created_at,
        updated_at=user_book.updated_at,
        title=book.title if book else None,
        authors=book.authors.split(", ") if book and book.authors else [],
        cover_url=book.cover_url if book else None,
        published_year=book.published_year if book else None
    )



@router.get("/", response_model=list[UserBookSchema], summary="Get user's reading list",)
async def get_user_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ReadingStatus | None = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Retrieve the current user's personal reading list.

    - Optional filtering by `status` (PLANNED, READING, COMPLETED)
    - Pagination supported via `page` and `page_size`
    - Returns full book details (title, authors, cover, year) along with user progress and rating
    """

    offset = (page - 1) * page_size

    query = (
        select(UserBookModel, BookModel)
        .outerjoin(BookModel, BookModel.work_olid == UserBookModel.work_olid)
        .where(UserBookModel.user_id == current_user.id)
    )

    if status_filter:
        query = query.where(UserBookModel.status == status_filter)

    query = query.limit(page_size).offset(offset)

    result = await db.execute(query)
    rows = result.all()

    books_full = []

    for user_book, book in rows:
        books_full.append(
            UserBookSchema(
                id=user_book.id,
                work_olid=user_book.work_olid,
                status=user_book.status.value,
                progress_percent=user_book.progress_percent,
                rating=user_book.rating,
                started_at=user_book.started_at,
                finished_at=user_book.finished_at,
                created_at=user_book.created_at,
                updated_at=user_book.updated_at,
                title=book.title if book else None,
                authors=book.authors.split(", ") if book and book.authors else [],
                cover_url=book.cover_url if book else None,
                published_year=book.published_year if book else None
            )
        )

    return books_full


@router.patch("/{user_book_id}", response_model=UserBookSchema, summary="Update a book in user's reading list")
async def update_user_book(
    user_book_id: int,
    book_update: UserBookUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Partially update a book in the user's reading list.

    - Update `status`, `progress_percent`, and/or `rating`
    - Automatically sets `started_at` when status becomes READING
    - Automatically sets `finished_at` and `progress_percent=100` when status becomes COMPLETED or progress reaches 100%
    """

    user_book = await db.scalar(
        select(UserBookModel).where(
            UserBookModel.id == user_book_id,
            UserBookModel.user_id == current_user.id
        )
    )

    if not user_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User book not found"
        )

    update_data = book_update.model_dump(exclude_unset=True)

    # Status update
    if "status" in update_data:
        new_status = update_data["status"]
        user_book.status = new_status

        # If the status changed to READING and hasn't been started yet
        if new_status == ReadingStatus.READING and not user_book.started_at:
            user_book.started_at = datetime.now(UTC)
            user_book.finished_at = None

        # If the status changed to COMPLETED
        if new_status == ReadingStatus.COMPLETED:
            user_book.progress_percent = 100
            if not user_book.started_at:
                user_book.started_at = datetime.now(UTC)
            user_book.finished_at = datetime.now(UTC)

    # Progress update
    if "progress_percent" in update_data:
        new_progress = update_data["progress_percent"]

        if new_progress >= 100:
            user_book.progress_percent = 100
            user_book.status = ReadingStatus.COMPLETED
            if not user_book.started_at:
                user_book.started_at = datetime.now(UTC)
            user_book.finished_at = datetime.now(UTC)
        else:
            user_book.progress_percent = new_progress
            # If the status was COMPLETED but the progress was decreased
            if user_book.status == ReadingStatus.COMPLETED:
                user_book.status = ReadingStatus.READING
                user_book.finished_at = None

            # Set started_at if it's still null
            if user_book.status == ReadingStatus.READING and not user_book.started_at:
                user_book.started_at = datetime.now(UTC)

    # Rating update
    if "rating" in update_data:
        user_book.rating = update_data["rating"]

    await db.commit()
    await db.refresh(user_book)

    book = await db.scalar(
        select(BookModel).where(BookModel.work_olid == user_book.work_olid)
    )

    return UserBookSchema(
        id=user_book.id,
        work_olid=user_book.work_olid,
        status=user_book.status.value,
        progress_percent=user_book.progress_percent,
        rating=user_book.rating,
        started_at=user_book.started_at,
        finished_at=user_book.finished_at,
        created_at=user_book.created_at,
        updated_at=user_book.updated_at,
        title=book.title if book else None,
        authors=book.authors.split(", ") if book and book.authors else [],
        cover_url=book.cover_url if book else None,
        published_year=book.published_year if book else None
    )


@router.delete("/{user_book_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a book from user's reading list")
async def delete_user_book(
    user_book_id: int,
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Delete a book from the current user's personal reading list.
    """

    user_book = await db.scalar(
        select(UserBookModel).where(
            UserBookModel.id == user_book_id,
            UserBookModel.user_id == current_user.id
        )
    )

    if not user_book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User book not found"
        )

    await db.delete(user_book)
    await db.commit()
