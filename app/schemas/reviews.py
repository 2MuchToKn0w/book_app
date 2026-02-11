from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class ReviewCreate(BaseModel):
    """
    Schema for creating a review
    """
    rating: float = Field(..., ge=1.0, le=5.0, description="Review rating from 1 to 5")
    comment: str | None = Field(None, description="Review Comment")


class ReviewUpdate(BaseModel):
    """
    Schema for updating a review (partial update)
    """
    rating: float | None = Field(None, ge=1.0, le=5.0, description="Review rating from 1 to 5")
    comment: str | None = Field(None, description="Review Comment")


class Review(BaseModel):
    """
    Schema for returning a review
    """
    id: int = Field(..., description="Review Id")
    user_id: int = Field(..., description="User Id")
    rating: float = Field(..., ge=1.0, le=5.0, description="Review rating from 1 to 5")
    comment: str | None = Field(None, description="Review Comment")
    created_at: datetime = Field(..., description="Review Created At")
    updated_at: datetime | None = Field(None, description="Review Updated At")

    model_config = ConfigDict(from_attributes=True)


class ReviewList(BaseModel):
    """
    Schema for returning list of reviews with average rating
    """
    avg_rating: float | None = Field(None, ge=1.0, le=5.0, description="Average review rating from 1 to 5")
    reviews: list[Review] = Field(..., description="List of reviews for the book")

