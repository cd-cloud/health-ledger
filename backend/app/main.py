from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import BACKUP_DIR, BACKUP_ENABLED, BACKUP_RETENTION_DAYS, SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.database import Base, engine
from app.routers import auth, biomarkers, reports, trends
from app.services.backup_scheduler import start_backup_scheduler, stop_backup_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.database import SessionLocal
    from app.services.report_parser import ensure_biomarkers_in_db
    from app.services.normalizer import BiomarkerNormalizer
    db = SessionLocal()
    try:
        ensure_biomarkers_in_db(db, BiomarkerNormalizer())
    finally:
        db.close()

    scheduler = None
    if BACKUP_ENABLED and engine.url.database and engine.url.database != ":memory:":
        scheduler = start_backup_scheduler(
            src=Path(engine.url.database),
            dest_dir=BACKUP_DIR,
            retention_days=BACKUP_RETENTION_DAYS,
        )

    try:
        yield
    finally:
        stop_backup_scheduler(scheduler)


app = FastAPI(
    title="Health Tracker MVP",
    description="个人体检指标追踪 MVP API",
    version="0.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie=SESSION_COOKIE_NAME,
    max_age=SESSION_MAX_AGE,
)

app.include_router(auth.router)
app.include_router(reports.router)
app.include_router(biomarkers.router)
app.include_router(trends.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
