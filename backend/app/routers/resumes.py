import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import select
from dotenv import load_dotenv

from .auth import get_current_user
from ..db import SessionDep
from ..models import User, Job, Resume, ResumeRead

load_dotenv()
router = APIRouter()

UPLOAD_DIRECTORY = os.getenv("UPLOAD_DIRECTORY", "uploaded_resumes")
TEXT_DATA_DIRECTORY = os.getenv("TEXT_DATA_DIRECTORY", "extracted_text")

os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
os.makedirs(TEXT_DATA_DIRECTORY, exist_ok=True)


@router.post("/resumes", tags=["resumes"], status_code=201)
async def upload_resume(
    file: UploadFile,
    job_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    job = session.exec(
        select(Job).where(Job.id == job_id, Job.created_by == current_user.id)
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    file_extention = os.path.splitext(file.filename)[1]
    stored_filename = f"{current_user.id}_{job_id}_{int(datetime.now().timestamp())}{file_extention}"
    stored_path = os.path.join(UPLOAD_DIRECTORY, stored_filename)

    with open(stored_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        with open(stored_path, "r", encoding="utf-8", errors="ignore") as f:
            extracted_text = f.read()
    except Exception:
        extracted_text = ""

    extracted_filename = stored_filename + ".txt"
    extracted_path = os.path.join(TEXT_DATA_DIRECTORY, extracted_filename)

    with open(extracted_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    event = {
        "event": "uploaded",
        "timestamp": datetime.now().isoformat(),
        "extracted_text_path": extracted_path,
    }

    new_resume = Resume(
        job_id=job_id,
        user_id=current_user.id,
        file_path=stored_path,
        processing_log=[event],
    )

    session.add(new_resume)
    session.commit()
    session.refresh(new_resume)
    return ResumeRead.model_validate(new_resume)
