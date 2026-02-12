from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from app.models.user_books import ReadingStatus

class UserBookAdd(BaseModel):
    """
    Schema for adding a book to user_books
    """
    work_olid: str = Field(..., description="Open Library work OLID of the book")
    status: ReadingStatus = Field(ReadingStatus.PLANNED, description="Status of the book")
    progress_percent: int = Field(0, ge=0, le=100, description="Progress percentage of the book")
    rating: int | None = Field(None, ge=1, le=5, description="Rating of the book")


class UserBookUpdate(BaseModel):
    """
    Schema for updating a book
    """
    status: ReadingStatus | None = Field(None, description="Status of the book")
    progress_percent: int | None = Field(None, ge=0, le=100)
    rating: int | None = Field(None, ge=1, le=5)


class UserBook(BaseModel):
    """
    Returns book information to the user
    """
    id: int = Field(..., description="ID of the book")
    work_olid: str = Field(..., description="Open Library work OLID of the book")
    status: str = Field(..., description="Reading status of the book")
    progress_percent: int = Field(..., description="Progress percentage of the book")
    rating: int | None = Field(None, description="Rating of the book")
    started_at: datetime | None = Field(None, description="Date when the book was started")
    finished_at: datetime | None = Field(None, description="Date when the book was finished")
    created_at: datetime = Field(..., description="Date when the book was created")
    updated_at: datetime = Field(..., description="Date when the book was updated")

    # Book information from the local table
    title: str | None = Field(None, description="Book title")
    authors: list[str] = Field(default_factory=list, description="Book authors")
    cover_url: str | None = Field(None, description="Book cover url")
    published_year: int | None = Field(None, description="Book published year")

    model_config = ConfigDict(from_attributes=True)