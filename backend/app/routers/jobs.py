import os
import jwt
from pwdlib import PasswordHash
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from .auth import get_current_user

from ..db import SessionDep
from ..models import User, JobCreate, Job, JobRead

load_dotenv()
router = APIRouter()

@router.post("/jobs", tags=["jobs"])
async def create_job(
    job: JobCreate, 
    session: SessionDep, 
    current_user: User = Depends(get_current_user)):
    new_job = Job(
        title=job.title,
        description=job.description,
        created_by=current_user.id
    )
    session.add(new_job)
    session.commit()
    session.refresh(new_job)
    return JobRead.model_validate(new_job, from_attributes=True)

