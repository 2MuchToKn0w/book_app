from fastapi import APIRouter, Request, Query, HTTPException, status, Depends

from app.schemas.books import Book as BookSchema, BooksSearchItem, BooksSearchList
from app.schemas.reviews import Review as ReviewSchema, ReviewCreate, ReviewList
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.depends import get_async_db

from app.auth import get_current_user



router = APIRouter(
    prefix="/books",
    tags=["books"],
)


@router.get("/search", response_model=BooksSearchList)
async def search_books(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    title: str | None = Query(None, description="Book title"),
    authors: str | None = Query(None, description="Book authors"),
    year: int | None = Query(None, description="Book publishing year"),
    subject: str | None = Query(None, description="Book subject"),
    isbn: str | None = Query(None, description="Book ISBN"),
    publisher: str | None = Query(None, description="Book publisher"),
):
    """
    Returns a list of books based on specified filters with pagination support
    """
    service = request.app.state.open_library_service

    # Build search query parts from provided filters
    q_parts = []
    if title:
        q_parts.append(f'title:"{title}"')
    if authors:
        q_parts.append(f'author:"{authors}"')
    if year:
        q_parts.append(f'first_publish_year:{year}')
    if subject:
        q_parts.append(f'subject:"{subject}"')
    if isbn:
        q_parts.append(f'isbn:{isbn}')
    if publisher:
        q_parts.append(f'publisher:"{publisher}"')

    # Return empty result if no filters are provided
    if not q_parts:
        return BooksSearchList(items=[], total=0, page=page, page_size=page_size)

    # Combine query parts and calculate pagination offset
    q = " AND ".join(q_parts)
    offset = (page - 1) * page_size

    results = await service.search_books(query=q, offset=offset, limit=page_size)

    items = []
    for doc in results.get("docs", []):
        # Normalize authors list
        authors_list = []
        for a in doc.get("author_name", []):
            if isinstance(a, str):
                authors_list.append(a)
            elif isinstance(a, dict) and "name" in a:
                authors_list.append(a["name"])

        # Build cover image URL if available
        cover_url = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg" if doc.get("cover_i") else None

        items.append(
            BooksSearchItem(
                work_olid=doc.get("key", "").split("/")[-1],
                title=doc.get("title"),
                authors=authors_list or None,
                year=doc.get("first_publish_year"),
                cover_url=cover_url,
            )
        )

    return BooksSearchList(
        items=items,
        total=results.get("numFound", 0),
        page=page,
        page_size=page_size,
    )


@router.get("/{edition_olid}", response_model=BookSchema)
async def get_book_by_edition(edition_id: str, request: Request):
    """
    Returns detailed book information by edition OLID
    """
    service = request.app.state.open_library_service
    book_data = await service.get_book_by_edition(edition_id)

    if not book_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This book not found")

    return BookSchema(**book_data)


@router.post("{work_olid}/reviews", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
        work_olid: str,
        review: ReviewCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
        request: Request = None,
):
    """
    Creates new review
    """

    # Check if the book exists via Open Library
    service = request.app.state.open_library_service
    book_data = await service.get_book_by_work(work_olid)

    if not book_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    # Check if the user has already left a review
    existing_review = await db.scalar(
        select(ReviewModel)
        .where(ReviewModel.user_id == current_user.id,
               ReviewModel.work_olid == work_olid
               )
    )

    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this book"
        )

    new_review = ReviewModel(
        work_olid=work_olid,
        user_id=current_user.id,
        rating=review.rating,
        comment=review.comment
    )

    db.add(new_review)
    await db.commit()
    await db.refresh(new_review)

    return new_review


@router.get("/{work_olid}/reviews", response_model=ReviewList)
async def get_review_list(
        work_olid: str,
        db: AsyncSession = Depends(get_async_db),
        request: Request = None,
):
    """
    Returns review list
    """

    service = request.app.state.open_library_service
    book_data = await service.get_book_by_work(work_olid)

    if not book_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")

    result = await db.execute(
        select(ReviewModel)
        .where(ReviewModel.work_olid == work_olid)
    )
    reviews = result.scalars().all()

    if not reviews:
        avg_rating = None
    else:
        avg_rating = await db.scalar(
            select(func.avg(ReviewModel.rating))
            .where(ReviewModel.work_olid == work_olid)
        )
        avg_rating = round(float(avg_rating), 2)

    return ReviewList(
        avg_rating=avg_rating,
        reviews=reviews
    )