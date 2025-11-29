from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status

from .db import create_db_and_tables
from .routers import auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
