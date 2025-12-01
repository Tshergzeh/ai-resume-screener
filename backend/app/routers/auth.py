import os
import jwt
from pwdlib import PasswordHash
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from ..db import SessionDep
from ..models import UserRegister, User, UserRead, UserLogin

load_dotenv()
router = APIRouter()
ph = PasswordHash.recommended()

SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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

@router.post("/auth/login", tags=["auth"])
async def login(user: UserLogin, session: SessionDep):
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    try:
        ph.verify(user.password, db_user.password)
    except:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_access_token({"sub": str(db_user.id)})
    return {"access_token": token, "token_type": "bearer", "user": UserRead.model_validate(db_user)}
