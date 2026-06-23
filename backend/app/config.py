import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
BACKUP_DIR = BASE_DIR / "backups"
DOCS_DIR = BASE_DIR / "docs"

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'healthtracker.db'}")

BACKUP_ENABLED = os.getenv("BACKUP_ENABLED", "true").lower() in ("1", "true", "yes")
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "7"))

KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "kimi")

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 天

MEDICAL_DISCLAIMER = (
    "以上分析仅供参考，不构成医疗诊断或治疗建议。"
    "如有异常请咨询专业医生，并以医院出具的正式报告为准。"
)
