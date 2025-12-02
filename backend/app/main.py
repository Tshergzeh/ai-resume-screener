from contextlib import asynccontextmanager
from fastapi import FastAPI

from .db import create_db_and_tables
from .routers import auth, jobs, resumes

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(resumes.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
