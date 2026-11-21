from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, auth, automation, guardian, health, quantum
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401 — register all models before create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://192.168.192.128:8080",
        "http://localhost:8000",
        "http://localhost:8501",
        "https://zithaewarty-11.github.io",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(quantum.router)
app.include_router(automation.router)
app.include_router(guardian.router)
app.include_router(ai.router)
