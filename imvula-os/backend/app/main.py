from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ai, auth, automation, guardian, health, quantum
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401 — register all models before create_all

# NOTE: create_all is used for local SQLite development only.
# In production, Alembic migrations (Step 2) manage the schema.
if settings.environment != "production":
    Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list(),
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
