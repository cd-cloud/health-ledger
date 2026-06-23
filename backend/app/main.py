from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import SECRET_KEY, SESSION_COOKIE_NAME, SESSION_MAX_AGE
from app.database import Base, engine
from app.routers import auth, biomarkers, reports, trends


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
    yield


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
