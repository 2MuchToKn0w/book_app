from pydantic import BaseModel, Field, ConfigDict, EmailStr

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