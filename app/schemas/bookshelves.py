from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

from app.schemas.books_in_shelf import BookInShelf


class BookShelf(BaseModel):
    """
    Basic information about BookShelf
    """
    id: int = Field(..., description="List id")
    name: str = Field(..., description="List name")
    description: str | None = Field(None, description="List description")
    created_at: datetime | None = Field(None, description="List created at")
    books: list[BookInShelf] = Field(default_factory=list, description="Books in the shelf")

    model_config = ConfigDict(from_attributes=True)


class BookShelfCreate(BaseModel):
    """
    Schema for creating a new BookShelf
    """
    name: str = Field(..., description="List name")
    description: str | None = Field(None, description="List description")


class BookShelfUpdate(BaseModel):
    """
    Schema for updating a bookshelf
    """
    name: str | None = Field(None, description="List name")
    description: str | None = Field(None, description="List description")


class BookShelfList(BookShelf):
    """
    Full list of books in a specific BookShelf
    """
    pass