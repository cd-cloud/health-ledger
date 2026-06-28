import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import BACKUP_DIR, BACKUP_ENABLED, BACKUP_RETENTION_DAYS

logger = logging.getLogger(__name__)


def backup_database(src: Path, dest_dir: Path, timestamp: datetime | None = None) -> Path:
    """将 SQLite 数据库文件复制到备份目录，按日命名。

    注意：备份文件包含用户敏感健康数据，请妥善保管并限制访问权限。
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    ts = timestamp or datetime.now()
    dest_name = f"healthtracker_{ts.strftime('%Y-%m-%d')}.db"
    dest_path = dest_dir / dest_name

    # 若同日备份已存在，追加时分秒后缀避免覆盖
    if dest_path.exists():
        dest_name = f"healthtracker_{ts.strftime('%Y-%m-%d_%H%M%S')}.db"
        dest_path = dest_dir / dest_name

    shutil.copy2(src, dest_path)
    logger.info("数据库已备份至 %s", dest_path)
    return dest_path


def cleanup_old_backups(dest_dir: Path, retention_days: int) -> int:
    """清理超过保留天数的旧备份，返回删除文件数量。"""
    dest_dir = Path(dest_dir)
    if not dest_dir.exists():
        return 0

    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0
    for path in dest_dir.glob("healthtracker_*.db"):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if mtime < cutoff:
                path.unlink()
                removed += 1
                logger.info("已清理过期备份: %s", path)
        except Exception:
            logger.exception("清理旧备份失败: %s", path)
    return removed


def _run_backup_job(src: Path, dest_dir: Path, retention_days: int) -> None:
    """定时任务入口：执行备份并清理过期文件。"""
    try:
        backup_database(src, dest_dir)
        cleanup_old_backups(dest_dir, retention_days)
    except Exception:
        logger.exception("定时备份任务执行失败")


def start_backup_scheduler(
    src: Path,
    dest_dir: Path = BACKUP_DIR,
    retention_days: int = BACKUP_RETENTION_DAYS,
    run_now: bool = False,
) -> Optional[BackgroundScheduler]:
    """启动后台定时备份调度器，默认每日 02:00 执行。"""
    if not BACKUP_ENABLED:
        logger.info("自动备份已禁用")
        return None

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_backup_job,
        trigger=CronTrigger(hour=2, minute=0),
        args=(Path(src), Path(dest_dir), retention_days),
        id="daily_database_backup",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("自动备份调度器已启动，源: %s，目标: %s", src, dest_dir)

    if run_now:
        _run_backup_job(Path(src), Path(dest_dir), retention_days)

    return scheduler


def stop_backup_scheduler(scheduler: Optional[BackgroundScheduler]) -> None:
    """安全关闭备份调度器。"""
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("自动备份调度器已关闭")
