from fastapi import APIRouter, HTTPException
from sqlmodel import select
from argon2 import PasswordHasher

from ..db import SessionDep
from ..models import UserRegister, User, UserRead

router = APIRouter()
ph = PasswordHasher()

@router.post("/auth/register", tags=["auth"])
async def register(user: UserRegister, session: SessionDep):
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user.email,
        name=user.name,
        password=ph.hash(user.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return UserRead.model_validate(new_user)
