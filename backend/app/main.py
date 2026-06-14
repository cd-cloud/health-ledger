from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import reports, biomarkers, trends


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
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router)
app.include_router(biomarkers.router)
app.include_router(trends.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
