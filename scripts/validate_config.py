"""
Validate configuration and environment variables.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.config import load_yaml_config
from src.storage.db import test_connection


def validate_config():
    """Validate all configuration and environment variables."""
    errors = []
    warnings = []
    
    print("Validating configuration...\n")
    
    # Check database connection
    print("1. Checking database connection...")
    if test_connection():
        print("   [OK] Database connection successful")
    else:
        errors.append("Database connection failed")
        print("   [ERROR] Database connection failed")
    
    # Check required environment variables
    print("\n2. Checking environment variables...")
    required_vars = []
    optional_vars = {
        "YOUTUBE_API_KEY": "YouTube ingestion will be disabled",
        "REDDIT_CLIENT_ID": "Reddit ingestion will be disabled",
        "REDDIT_CLIENT_SECRET": "Reddit ingestion will be disabled",
    }
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
            print(f"   [ERROR] Missing {var}")
        else:
            print(f"   [OK] {var} is set")
    
    for var, message in optional_vars.items():
        if not os.getenv(var):
            warnings.append(f"{var} not set: {message}")
            print(f"   [WARN] {var} not set: {message}")
        else:
            print(f"   [OK] {var} is set")
    
    # Check configuration files
    print("\n3. Checking configuration files...")
    config_files = {
        "config/sources.yaml": "Source configuration",
        "config/weights.yaml": "Weight configuration",
        "config/pinned_entities.json": "Entity catalog",
    }
    
    for config_file, description in config_files.items():
        config_path = Path(config_file)
        if config_path.exists():
            try:
                if config_file.endswith(".yaml"):
                    load_yaml_config(config_file)
                print(f"   [OK] {description} ({config_file})")
            except Exception as e:
                errors.append(f"Invalid {description}: {e}")
                print(f"   [ERROR] {description} ({config_file}): {e}")
        else:
            errors.append(f"Missing configuration file: {config_file}")
            print(f"   [ERROR] Missing {config_file}")
    
    # Check data directory
    print("\n4. Checking data directory...")
    data_dir = Path("data")
    if data_dir.exists() or os.getenv("DATABASE_URL", "").startswith("postgresql"):
        print("   [OK] Data directory exists or using Postgres")
    else:
        data_dir.mkdir(exist_ok=True)
        print("   [OK] Created data directory")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"[ERROR] Validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        print("\nPlease fix the errors above before running the application.")
        return False
    elif warnings:
        print(f"[WARN] Validation passed with {len(warnings)} warning(s):")
        for warning in warnings:
            print(f"  - {warning}")
        print("\nApplication should work, but some features may be disabled.")
        return True
    else:
        print("[SUCCESS] All configuration valid!")
        return True


def main():
    """Entry point for script execution."""
    success = validate_config()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
