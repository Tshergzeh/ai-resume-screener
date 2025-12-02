import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, Dict, Any, List
from functools import partial
from sqlalchemy import Text, Column, Enum as SQLEnum
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

# User models

class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    name: Optional[str] = Field(default=None, max_length=255)
    password: str = Field(max_length=128)
    jobs: list["Job"] = Relationship(back_populates="user")

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRead(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None

# Job models

class Job(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    title: str = Field(max_length=255)
    description: str = Field(sa_type=Text)
    created_by: str = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    user: Optional[User] = Relationship(back_populates="jobs")
    resumes: list["Resume"] = Relationship(back_populates="job")
    
class JobCreate(BaseModel):
    title: str
    description: str

class JobRead(BaseModel):
    id: str
    title: str
    description: str
    created_by: str
    created_at: datetime

class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

# Resume models

class ResumeStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class Resume(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    job_id: str = Field(foreign_key="job.id", index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    file_path: str
    parsed_data: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Field(sa_column=JSONB)
    )
    score: Optional[float] = None
    status: ResumeStatus = Field(
        default=ResumeStatus.PENDING,
        sa_column=Column(SQLEnum(ResumeStatus))
    )
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=3)
    processing_log: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list,
        sa_column=Field(sa_column=JSONB)
    )
    created_at: datetime = Field(default_factory=partial(datetime.now, timezone.utc))
    job: Optional[Job] = Relationship(back_populates="resumes")

class ResumeRead(BaseModel):
    id: str
    job_id: str
    file_path: str
    extracted_data: Optional[str]
    parsed_data: Optional[Dict[str, Any]]
    score: Optional[float]
    status: ResumeStatus
    created_at: datetime

    class Config:
        from_attributes = True
    