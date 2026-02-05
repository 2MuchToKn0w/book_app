from sqlalchemy import Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.favorites import Favorite


class User(Base):
    """
    Represents a user in the system
    """
    __tablename__ = 'users'

    # Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    username: Mapped[str] = mapped_column(String(25), nullable=False)
    role: Mapped[str] = mapped_column(String, default='user')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationship
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan"
    )