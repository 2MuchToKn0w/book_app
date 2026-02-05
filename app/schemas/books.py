from pydantic import BaseModel, Field, ConfigDict

class Book(BaseModel):
    """
    Detailed book information
    """
    work_olid: str = Field(..., description="Work OLID")  # new
    title: str | None = Field(None, description="Book title")
    authors: list[str] | None = Field(None, description="Authors names")
    description: str | None = Field(None, description="Book description")
    language: list[str] | None = Field(None, description="Book language")
    year: int | None = Field(None, description="First published year")
    isbn: list[str] | None = Field(None, description="Book ISBN")
    pages: int | None = Field(None, description="Book pages")
    cover_url: str | None = Field(None, description="Cover URL")
    subject: list[str] | None = Field(None, description="Book subject")
    publisher: list[str] | None = Field(None, description="Book publisher")

    model_config = ConfigDict(from_attributes=True)


class BooksSearchItem(BaseModel):
    """
    Short book information for search results
    """
    work_olid: str = Field(..., description="Book ID (work_olid) – fetch details on click.")  # new
    title: str | None = Field(None, description="Book title")
    authors: list[str] | None = Field(None, description="Authors names")
    year: int | None = Field(None, description="First published year")
    cover_url: str | None = Field(None, description="Book cover URL")

    model_config = ConfigDict(from_attributes=True)


class BooksSearchList(BaseModel):
    """
    Paginated list of books returned from a search
    """
    items: list[BooksSearchItem] = Field(description="Book for current page")
    total: int = Field(ge=0, description="Total number of books")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Books per page")

    model_config = ConfigDict(from_attributes=True)