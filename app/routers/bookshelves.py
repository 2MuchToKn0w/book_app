from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.depends import get_async_db
from app.models.bookshelves import BookShelf as BookShelfModel
from app.models.books_in_shelf import BookInShelf as BookInShelfModel
from app.models.users import User as UserModel

from app.schemas.bookshelves import BookShelf as BookShelfSchema, BookShelfCreate, BookShelfList
from app.schemas.books_in_shelf import BookInShelf as BookInShelfSchema, BookAdd
from app.auth import get_current_user

import httpx
import asyncio
from app.services.open_library import OpenLibraryService, BASE_URL


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

    return [
        BookShelfSchema(
            id=b.id,
            name=b.name,
            description=b.description,
            created_at=b.created_at,
            books=[]
        )
        for b in bookshelves
    ]


@router.post("/{bookshelf_id}/books", response_model=BookInShelfSchema, status_code=status.HTTP_201_CREATED)
async def add_book_in_shelf(
        bookshelf_id: int,
        book_data: BookAdd,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Add a book to a user's bookshelf
    """

    # Check that bookshelf exists and belongs to current user
    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.id == bookshelf_id,
            BookShelfModel.user_id == current_user.id,
        )
    )
    bookshelf = result.scalars().first()

    if not bookshelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookshelf not found"
        )

    # Check if the book is already in the bookshelf
    result = await db.execute(
        select(BookInShelfModel).where(
            BookInShelfModel.bookshelf_id == bookshelf.id,
            BookInShelfModel.work_olid == book_data.work_olid,
        )
    )
    existing_book = result.scalars().first()

    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book is already in the bookshelf"
        )

    book_in_shelf = BookInShelfModel(
        bookshelf_id=bookshelf.id,
        work_olid=book_data.work_olid,
    )

    db.add(book_in_shelf)
    await db.commit()
    await db.refresh(book_in_shelf)

    return BookInShelfSchema(
        id=book_in_shelf.id,
        work_olid=book_in_shelf.work_olid,
        added_at=book_in_shelf.added_at
    )


@router.get("/{bookshelf_id}", response_model=BookShelfList)
async def get_bookshelf(
        bookshelf_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Get a specific bookshelf along with full details of all books in it
    """
    
    # Get a specific bookshelf from the database for the current user
    result = await db.execute(
        select(BookShelfModel)
        .where(BookShelfModel.id == bookshelf_id,
               BookShelfModel.user_id == current_user.id)
        .options(selectinload(BookShelfModel.books))
    )
    bookshelf = result.scalars().first()
    if not bookshelf:
        raise HTTPException(status_code=404, detail="Bookshelf not found")

    # Fetch full information about books via Open Library
    books_full = []
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        ol_service = OpenLibraryService(client)
        # Use asyncio.gather for parallel requests
        books_full = await asyncio.gather(*[
            ol_service.get_book_by_work(book.work_olid)
            for book in bookshelf.books
        ])

    # Add local database data to each book object
    for i, book in enumerate(books_full):
        book["id"] = bookshelf.books[i].id
        book["added_at"] = bookshelf.books[i].added_at

    return BookShelfList(
        id=bookshelf.id,
        name=bookshelf.name,
        description=bookshelf.description,
        created_at=bookshelf.created_at,
        books=books_full
    )