from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class BookInShelf(BaseModel):
    """
    Full information about a book in a bookshelf
    """
    id: int = Field(..., description="Book ID in the shelf")
    work_olid: str = Field(..., description="Open Library work OLID of the book")
    title: str | None = Field(None, description="Book title")
    authors: list[str] = Field(default_factory=list, description="Book authors")
    year: int | None = Field(None, description="Publication year")
    cover_url: str | None = Field(None, description="URL of book cover")
    added_at: datetime | None = Field(None, description="When the book was added to the shelf")

    model_config = ConfigDict(from_attributes=True)


class BookAdd(BaseModel):
    """
    Schema for adding a book to a bookshelf
    """
    work_olid: str = Field(..., description="Open Library work OLID of the book")

