import uuid

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel
from typing import Optional

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    name: Optional[str] = Field(default=None, max_length=255)
    password: str = Field(max_length=128)

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(SQLModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
