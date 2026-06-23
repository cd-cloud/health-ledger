import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.services.backup_scheduler import (
    backup_database,
    cleanup_old_backups,
    start_backup_scheduler,
    stop_backup_scheduler,
)


class TestBackupDatabase:
    def test_backup_creates_timestamped_file(self, tmp_path):
        src = tmp_path / "source.db"
        src.write_text("hello backup")
        dest_dir = tmp_path / "backups"

        dest_path = backup_database(src, dest_dir)

        assert dest_path.exists()
        assert dest_path.parent == dest_dir
        assert dest_path.name.startswith("healthtracker_")
        assert dest_path.suffix == ".db"
        assert dest_path.read_text() == "hello backup"

    def test_backup_does_not_overwrite_same_day(self, tmp_path):
        src = tmp_path / "source.db"
        src.write_text("v1")
        dest_dir = tmp_path / "backups"
        ts = datetime(2026, 6, 23, 10, 0, 0)

        first = backup_database(src, dest_dir, timestamp=ts)
        src.write_text("v2")
        second = backup_database(src, dest_dir, timestamp=ts)

        assert first != second
        assert first.read_text() == "v1"
        assert second.read_text() == "v2"


class TestCleanupOldBackups:
    def test_removes_only_expired_backups(self, tmp_path):
        dest_dir = tmp_path / "backups"
        dest_dir.mkdir()

        old_file = dest_dir / "healthtracker_2026-06-01.db"
        old_file.write_text("old")
        # 修改 mtime 为 10 天前
        old_mtime = time.mktime((datetime.now() - timedelta(days=10)).timetuple())
        old_file.touch()
        os.utime(old_file, (old_mtime, old_mtime))

        new_file = dest_dir / "healthtracker_2026-06-23.db"
        new_file.write_text("new")

        removed = cleanup_old_backups(dest_dir, retention_days=7)

        assert removed == 1
        assert not old_file.exists()
        assert new_file.exists()

    def test_cleanup_on_missing_directory(self, tmp_path):
        dest_dir = tmp_path / "does_not_exist"
        removed = cleanup_old_backups(dest_dir, retention_days=7)
        assert removed == 0


class TestBackupScheduler:
    def test_start_stop_scheduler(self, tmp_path):
        src = tmp_path / "source.db"
        src.write_text("data")
        dest_dir = tmp_path / "backups"

        scheduler = start_backup_scheduler(src, dest_dir, retention_days=7)
        assert scheduler is not None
        assert scheduler.running

        stop_backup_scheduler(scheduler)
        assert not scheduler.running

    def test_start_scheduler_respects_disabled_flag(self, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.backup_scheduler.BACKUP_ENABLED", False)
        src = tmp_path / "source.db"
        src.write_text("data")
        dest_dir = tmp_path / "backups"

        scheduler = start_backup_scheduler(src, dest_dir, retention_days=7)
        assert scheduler is None
