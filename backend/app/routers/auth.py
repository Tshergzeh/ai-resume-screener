import os
from typing import Annotated
import jwt
from pwdlib import PasswordHash
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

from ..db import SessionDep
from ..models import UserRegister, User, UserRead, UserLogin

load_dotenv()
router = APIRouter()
ph = PasswordHash.recommended()
security = HTTPBearer()

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

async def get_current_user(
        token: Annotated[HTTPAuthorizationCredentials, Depends(security)], 
        session: SessionDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        print(payload)
        user_id = payload.get("sub")
        print(user_id)
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise credentials_exception
    return UserRead.model_validate(user, from_attributes=True)

@router.post("/auth/register", tags=["auth"], status_code=201)
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
    
    token = create_access_token({"sub": str(db_user.id)}, expires_delta=timedelta(days=7))
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": UserRead.model_validate(db_user, from_attributes=True)}
