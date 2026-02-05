from sqlalchemy import Integer, String, DateTime, func, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.users import User


class Favorite(Base):
    """
    Represents a favorite book saved by the user
    """
    __tablename__ = 'favorites'

    # Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_olid: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    authors: Mapped[str | None] = mapped_column(String, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Foreign key
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="favorites")

    # Constraint
    __table_args__ = (
        UniqueConstraint("work_olid", "user_id", name="uq_favorite_work_user"),
    )
