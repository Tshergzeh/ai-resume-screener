import os
import jwt
from pwdlib import PasswordHash
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from .auth import get_current_user

from ..db import SessionDep
from ..models import User, JobCreate, Job, JobRead, JobUpdate

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

@router.get("/jobs", tags=["jobs"])
async def read_jobs(
    session: SessionDep,
    current_user: User = Depends(get_current_user)):
    jobs = session.exec(select(Job).where(Job.created_by == current_user.id)).all()
    return [JobRead.model_validate(job, from_attributes=True) for job in jobs]

@router.get("/jobs/{job_id}", tags=["jobs"])
async def read_job(
    job_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user)):
    job = session.exec(
        select(Job).where(Job.id == job_id, Job.created_by == current_user.id)
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobRead.model_validate(job, from_attributes=True)

@router.put("/jobs/{job_id}", tags=["jobs"])
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    session: SessionDep,
    current_user: User = Depends(get_current_user)):
    job = session.exec(
        select(Job).where(Job.id == job_id, Job.created_by == current_user.id)
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job_update.title is not None:
        job.title = job_update.title
    if job_update.description is not None:
        job.description = job_update.description
    session.add(job)
    session.commit()
    session.refresh(job)
    return JobRead.model_validate(job, from_attributes=True)

@router.delete("/jobs/{job_id}", tags=["jobs"], status_code=204)
async def delete_job(
    job_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user)):
    job = session.exec(
        select(Job).where(Job.id == job_id, Job.created_by == current_user.id)
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    session.delete(job)
    session.commit()

