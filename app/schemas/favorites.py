from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime

class Favorite(BaseModel):
    """
    Favorite book information
    """
    id: int = Field(..., title="Favorite ID")
    work_olid: str = Field(..., title="Olid ID")
    title: str | None = Field(None, title="Book title")
    authors: list[str] | None = Field(None, title="Book author")
    year: int | None = Field(None, description="First published year")
    cover_url: str | None = Field(None, title="Cover URL")
    created_at: datetime | None = Field(None, title="Created at")

    @field_validator("authors", mode="before")
    @classmethod
    def split_authors(cls, v):
        # Normalize authors field
        if isinstance(v, str):
            return [author.strip() for author in v.split(",")]
        return v

    model_config = ConfigDict(from_attributes=True)


class FavoriteList(BaseModel):
    """
    Paginated list of favorite books
    """
    items: list[Favorite] = Field(description="Favorite books on this page")
    total: int = Field(ge=0, description="Total number of favorite books")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Books per page")

    model_config = ConfigDict(from_attributes=True)

