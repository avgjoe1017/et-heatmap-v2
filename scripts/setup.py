"""
Setup script for ET Heatmap project.
Initializes database and syncs pinned entities.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.migrate_db import run_migrations
from src.catalog.catalog_loader import sync_pinned_to_db
from src.storage.db import test_connection, init_db


def setup():
    """Run initial setup."""
    print("Setting up ET Heatmap project...\n")
    
    # Test database connection
    print("1. Testing database connection...")
    if test_connection():
        print("   [OK] Database connection successful\n")
    else:
        print("   [WARN] Database connection failed, initializing database...")
        init_db()
        if test_connection():
            print("   [OK] Database initialized successfully\n")
        else:
            print("   [ERROR] Failed to initialize database")
            sys.exit(1)
    
    # Run migrations
    print("2. Running database migrations...")
    try:
        run_migrations()
        print("   [OK] Migrations completed\n")
    except Exception as e:
        print(f"   [ERROR] Migration failed: {e}")
        sys.exit(1)
    
    # Sync pinned entities
    print("3. Syncing pinned entities to database...")
    try:
        sync_pinned_to_db()
        print("   [OK] Pinned entities synced\n")
    except Exception as e:
        print(f"   [WARN] Failed to sync pinned entities: {e}\n")
    
    print("Setup complete! [SUCCESS]")
    print("\nNext steps:")
    print("  - Install Python dependencies: pip install -e .")
    print("  - Install UI dependencies: cd ui && npm install")
    print("  - Start API server: python -m src.app.main")
    print("  - Start UI dev server: cd ui && npm run dev")


if __name__ == "__main__":
    setup()
