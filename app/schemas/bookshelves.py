from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class BookShelf(BaseModel):
    """
    Basic information about BookShelf
    """
    id: int = Field(..., description="List id")
    name: str = Field(..., description="List name")
    description: str | None = Field(None, description="List description")
    created_at: datetime | None = Field(None, description="List created at")

    model_config = ConfigDict(from_attributes=True)


class BookShelfCreate(BaseModel):
    """
    Schema for creating a new BookShelf
    """
    name: str = Field(..., description="List name")
    description: str | None = Field(None, description="List description")