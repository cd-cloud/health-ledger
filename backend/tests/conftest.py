import json
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base, get_db
from app.main import app
from app.services.auth import hash_password
from app.services.normalizer import BiomarkerNormalizer
from app.services.report_parser import ensure_biomarkers_in_db


def _run_migrations_for_database(url: str) -> None:
    """对指定数据库 URL 执行 Alembic 升级到最新版本。"""
    alembic_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="function")
def db(tmp_path):
    """每个测试函数使用全新的文件数据库。"""
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    _run_migrations_for_database(f"sqlite:///{db_path.as_posix()}")
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(scope="function")
def client(db):
    """返回使用测试数据库的 TestClient。"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    @asynccontextmanager
    async def test_lifespan(app):
        ensure_biomarkers_in_db(db, BiomarkerNormalizer())
        yield

    app.dependency_overrides[get_db] = override_get_db
    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = test_lifespan
    yield TestClient(app)
    app.dependency_overrides.clear()
    app.router.lifespan_context = original_lifespan


@pytest.fixture(scope="function")
def normalizer():
    return BiomarkerNormalizer()


@pytest.fixture(scope="function")
def sample_biomarkers(db):
    """向测试数据库写入示例指标字典。"""
    normalizer = BiomarkerNormalizer()
    for b in normalizer.list_biomarkers():
        db.add(
            models.Biomarker(
                code=b["code"],
                name=b["name"],
                aliases=json.dumps(b.get("aliases", []), ensure_ascii=False),
                unit_standard=b["unit_standard"],
                unit_aliases=json.dumps(b.get("unit_aliases", []), ensure_ascii=False),
                category=b.get("category"),
                reference_low=b.get("reference_low"),
                reference_high=b.get("reference_high"),
                direction=b.get("direction"),
                description=b.get("description"),
            )
        )
    db.commit()
    return normalizer.list_biomarkers()


@pytest.fixture(scope="function")
def test_user(db):
    """创建一个测试用户并返回。"""
    user = models.User(
        username="testuser",
        hashed_password=hash_password("testpass"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_client(client, test_user):
    """返回已登录测试用户的 TestClient。"""
    response = client.post(
        "/auth/login",
        json={"username": test_user.username, "password": "testpass"},
    )
    assert response.status_code == 200
    yield client
