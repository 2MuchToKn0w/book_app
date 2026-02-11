from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Literal
from datetime import datetime

class UserOut(BaseModel):
    """
    Schema representing a user for admin responses
    """
    id: int = Field(description="ID of the user")
    email: EmailStr = Field(description="Email address of the user")
    username: str = Field(description="Username of the user")
    role: str = Field(description="Role of the user")
    is_active: bool = Field(description="Is active?")
    created_at: datetime = Field(..., title="Created at")

    model_config = ConfigDict(from_attributes=True)


class UpdateUserRole(BaseModel):
    """
    Schema for updating a user's role and status
    """
    role: Literal['user', 'admin'] | None = Field(None, description="Role of the user")
    is_active: bool | None = Field(None, description="Is active?")


class AdminReviewUpdate(BaseModel):
    """
    Schema for admin to update a review's comment
    """
    comment: str | None = Field(None, description="New text of the review comment")