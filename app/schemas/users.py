from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Literal

class UserCreate(BaseModel):
    """
    Schema for creating a new user
    """
    email: EmailStr = Field(description="Email address of the user")
    password: str = Field(min_length=8, description="Password of the user (minimum 8 characters)")
    username: str = Field(max_length=25, description="Username of the user")


class User(BaseModel):
    """
    Schema for returning user data
    """
    id: int = Field(description="ID of the user")
    email: EmailStr = Field(description="Email address of the user")
    username: str = Field(description="Username of the user")
    role: str = Field(description="Role of the user")
    is_active: bool = Field(description="Is active?")

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """
    Schema for updating a user
    """
    username: str | None = Field(None, description="Username of the user")
    role: Literal["user", "admin"] | None = Field(None, description="Role of the user")
    is_active: bool | None = Field(None, description="Is active?")


class RefreshTokenRequest(BaseModel):
    """
    Schema for sending a refresh token to obtain new JWT tokens
    """
    refresh_token: str = Field(description="Refresh token")