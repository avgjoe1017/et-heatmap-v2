#!/usr/bin/env python3
"""
Database backup script for ET Heatmap.

Supports both SQLite and PostgreSQL databases with automatic rotation and compression.
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
import gzip
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.logging import setup_logging

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Manage database backups with rotation and compression."""

    def __init__(
        self,
        backup_dir: str = "backups",
        keep_daily: int = 7,
        keep_weekly: int = 4,
        keep_monthly: int = 12,
        compress: bool = True,
    ):
        """
        Initialize backup manager.

        Args:
            backup_dir: Directory to store backups
            keep_daily: Number of daily backups to retain
            keep_weekly: Number of weekly backups to retain
            keep_monthly: Number of monthly backups to retain
            compress: Whether to compress backups (gzip)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.keep_daily = keep_daily
        self.keep_weekly = keep_weekly
        self.keep_monthly = keep_monthly
        self.compress = compress

    def backup_sqlite(self, db_path: str) -> Path:
        """
        Backup SQLite database.

        Args:
            db_path: Path to SQLite database file

        Returns:
            Path to backup file
        """
        db_file = Path(db_path)

        if not db_file.exists():
            raise FileNotFoundError(f"Database file not found: {db_path}")

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"et_heatmap_sqlite_{timestamp}.db"
        backup_path = self.backup_dir / backup_name

        logger.info(f"Creating SQLite backup: {backup_path}")

        # Copy database file
        shutil.copy2(db_file, backup_path)

        # Compress if enabled
        if self.compress:
            compressed_path = self._compress_file(backup_path)
            logger.info(f"Backup compressed: {compressed_path}")
            return compressed_path

        logger.info(f"Backup created successfully: {backup_path}")
        return backup_path

    def backup_postgres(self, connection_string: str) -> Path:
        """
        Backup PostgreSQL database using pg_dump.

        Args:
            connection_string: PostgreSQL connection string

        Returns:
            Path to backup file
        """
        import subprocess

        # Parse connection string
        # Format: postgresql://user:password@host:port/database
        if connection_string.startswith("postgresql://"):
            parts = connection_string.replace("postgresql://", "").split("@")
            if len(parts) == 2:
                user_pass = parts[0].split(":")
                host_db = parts[1].split("/")

                user = user_pass[0] if len(user_pass) > 0 else "postgres"
                password = user_pass[1] if len(user_pass) > 1 else ""
                host = host_db[0].split(":")[0] if len(host_db) > 0 else "localhost"
                port = host_db[0].split(":")[1] if ":" in host_db[0] else "5432"
                database = host_db[1] if len(host_db) > 1 else "et_heatmap"
            else:
                raise ValueError(f"Invalid PostgreSQL connection string: {connection_string}")
        else:
            raise ValueError(f"Invalid PostgreSQL connection string format: {connection_string}")

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"et_heatmap_postgres_{timestamp}.sql"
        backup_path = self.backup_dir / backup_name

        logger.info(f"Creating PostgreSQL backup: {backup_path}")

        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        # Run pg_dump
        try:
            cmd = [
                "pg_dump",
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                database,
                "-F",
                "c",  # Custom format (compressed)
                "-f",
                str(backup_path),
            ]

            subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
            logger.info(f"Backup created successfully: {backup_path}")

        except subprocess.CalledProcessError as e:
            logger.error(f"pg_dump failed: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error(
                "pg_dump not found. Install PostgreSQL client tools: "
                "apt-get install postgresql-client (Linux) or brew install postgresql (macOS)"
            )
            raise

        return backup_path

    def _compress_file(self, file_path: Path) -> Path:
        """Compress file using gzip."""
        compressed_path = file_path.with_suffix(file_path.suffix + ".gz")

        with open(file_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Remove original file
        file_path.unlink()

        return compressed_path

    def rotate_backups(self):
        """
        Rotate backups based on retention policy.

        Keeps:
        - Daily backups for last N days
        - Weekly backups (one per week) for last N weeks
        - Monthly backups (one per month) for last N months
        """
        now = datetime.now()

        # Get all backup files
        backup_files = sorted(self.backup_dir.glob("et_heatmap_*"), key=lambda p: p.stat().st_mtime)

        # Organize by date
        daily_backups = []
        weekly_backups = {}
        monthly_backups = {}

        for backup_file in backup_files:
            # Get file modification time
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            age_days = (now - mtime).days

            # Keep recent backups as daily
            if age_days < self.keep_daily:
                daily_backups.append(backup_file)
                continue

            # Group by week
            week_key = mtime.strftime("%Y-W%U")
            if week_key not in weekly_backups or mtime > datetime.fromtimestamp(
                weekly_backups[week_key].stat().st_mtime
            ):
                weekly_backups[week_key] = backup_file

            # Group by month
            month_key = mtime.strftime("%Y-%m")
            if month_key not in monthly_backups or mtime > datetime.fromtimestamp(
                monthly_backups[month_key].stat().st_mtime
            ):
                monthly_backups[month_key] = backup_file

        # Keep only recent weekly/monthly backups
        cutoff_weekly = now - timedelta(weeks=self.keep_weekly)
        cutoff_monthly = now - timedelta(days=30 * self.keep_monthly)

        keep_files = set(daily_backups)
        keep_files.update(
            [
                f
                for week, f in weekly_backups.items()
                if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff_weekly
            ]
        )
        keep_files.update(
            [
                f
                for month, f in monthly_backups.items()
                if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff_monthly
            ]
        )

        # Delete old backups
        deleted_count = 0
        for backup_file in backup_files:
            if backup_file not in keep_files:
                logger.info(f"Deleting old backup: {backup_file}")
                backup_file.unlink()
                deleted_count += 1

        logger.info(
            f"Backup rotation complete. Kept {len(keep_files)} backups, deleted {deleted_count}"
        )

    def restore_sqlite(self, backup_path: str, target_db_path: str):
        """
        Restore SQLite database from backup.

        Args:
            backup_path: Path to backup file
            target_db_path: Path to restore database to
        """
        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        target_file = Path(target_db_path)

        logger.info(f"Restoring SQLite database from: {backup_path}")

        # Decompress if needed
        if backup_file.suffix == ".gz":
            decompressed_path = backup_file.with_suffix("")
            with gzip.open(backup_file, "rb") as f_in:
                with open(decompressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_file = decompressed_path

        # Copy to target location
        shutil.copy2(backup_file, target_file)

        logger.info(f"Database restored successfully to: {target_db_path}")

    def restore_postgres(self, backup_path: str, connection_string: str):
        """
        Restore PostgreSQL database from backup using pg_restore.

        Args:
            backup_path: Path to backup file
            connection_string: PostgreSQL connection string
        """
        import subprocess

        backup_file = Path(backup_path)

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Parse connection string (same as backup_postgres)
        if connection_string.startswith("postgresql://"):
            parts = connection_string.replace("postgresql://", "").split("@")
            if len(parts) == 2:
                user_pass = parts[0].split(":")
                host_db = parts[1].split("/")

                user = user_pass[0] if len(user_pass) > 0 else "postgres"
                password = user_pass[1] if len(user_pass) > 1 else ""
                host = host_db[0].split(":")[0] if len(host_db) > 0 else "localhost"
                port = host_db[0].split(":")[1] if ":" in host_db[0] else "5432"
                database = host_db[1] if len(host_db) > 1 else "et_heatmap"
            else:
                raise ValueError(f"Invalid PostgreSQL connection string: {connection_string}")
        else:
            raise ValueError(f"Invalid PostgreSQL connection string format: {connection_string}")

        logger.info(f"Restoring PostgreSQL database from: {backup_path}")

        # Set PGPASSWORD environment variable
        env = os.environ.copy()
        if password:
            env["PGPASSWORD"] = password

        # Run pg_restore
        try:
            cmd = [
                "pg_restore",
                "-h",
                host,
                "-p",
                port,
                "-U",
                user,
                "-d",
                database,
                "--clean",  # Drop database objects before restoring
                "--if-exists",  # Don't error if objects don't exist
                str(backup_path),
            ]

            subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
            logger.info(f"Database restored successfully")

        except subprocess.CalledProcessError as e:
            logger.error(f"pg_restore failed: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error(
                "pg_restore not found. Install PostgreSQL client tools: "
                "apt-get install postgresql-client (Linux) or brew install postgresql (macOS)"
            )
            raise


def main():
    """Main backup script."""
    parser = argparse.ArgumentParser(description="ET Heatmap Database Backup")
    parser.add_argument(
        "--action",
        choices=["backup", "restore", "rotate"],
        default="backup",
        help="Action to perform (default: backup)",
    )
    parser.add_argument(
        "--db-url",
        default=os.getenv("DATABASE_URL", "sqlite:///./data/et_heatmap.db"),
        help="Database connection URL (default: from DATABASE_URL env var)",
    )
    parser.add_argument(
        "--backup-dir", default="backups", help="Backup directory (default: backups)"
    )
    parser.add_argument(
        "--backup-file", help="Backup file path (for restore action)"
    )
    parser.add_argument(
        "--no-compress", action="store_true", help="Disable compression"
    )
    parser.add_argument(
        "--keep-daily", type=int, default=7, help="Number of daily backups to keep (default: 7)"
    )
    parser.add_argument(
        "--keep-weekly", type=int, default=4, help="Number of weekly backups to keep (default: 4)"
    )
    parser.add_argument(
        "--keep-monthly",
        type=int,
        default=12,
        help="Number of monthly backups to keep (default: 12)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Initialize backup manager
    backup = DatabaseBackup(
        backup_dir=args.backup_dir,
        keep_daily=args.keep_daily,
        keep_weekly=args.keep_weekly,
        keep_monthly=args.keep_monthly,
        compress=not args.no_compress,
    )

    try:
        if args.action == "backup":
            # Perform backup
            if args.db_url.startswith("sqlite"):
                # Extract file path from SQLite URL
                db_path = args.db_url.replace("sqlite:///", "")
                backup_file = backup.backup_sqlite(db_path)
            elif args.db_url.startswith("postgresql"):
                backup_file = backup.backup_postgres(args.db_url)
            else:
                logger.error(f"Unsupported database type: {args.db_url}")
                sys.exit(1)

            logger.info(f"✅ Backup completed: {backup_file}")

            # Auto-rotate after backup
            backup.rotate_backups()

        elif args.action == "restore":
            if not args.backup_file:
                logger.error("--backup-file is required for restore action")
                sys.exit(1)

            # Perform restore
            if args.db_url.startswith("sqlite"):
                db_path = args.db_url.replace("sqlite:///", "")
                backup.restore_sqlite(args.backup_file, db_path)
            elif args.db_url.startswith("postgresql"):
                backup.restore_postgres(args.backup_file, args.db_url)
            else:
                logger.error(f"Unsupported database type: {args.db_url}")
                sys.exit(1)

            logger.info(f"✅ Restore completed")

        elif args.action == "rotate":
            # Just rotate backups
            backup.rotate_backups()
            logger.info(f"✅ Rotation completed")

    except Exception as e:
        logger.error(f"❌ Backup operation failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
