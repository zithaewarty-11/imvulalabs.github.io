from fastapi import FastAPI, Request
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

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


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
