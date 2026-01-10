"""
Run the daily pipeline with proper configuration validation.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Validate configuration before running
from scripts.validate_config import validate_config
from src.pipeline.daily_run import run_daily_pipeline

def main():
    """Entry point for script execution."""
    print("ET Heatmap Daily Pipeline\n")
    
    # Validate configuration
    if not validate_config():
        print("\n[ERROR] Configuration validation failed. Please fix errors before running the pipeline.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Starting pipeline run...")
    print("=" * 60 + "\n")
    
    try:
        # Run pipeline (uses latest window by default)
        window_start = None
        
        # Allow override via command line
        if len(sys.argv) > 1:
            try:
                window_start = datetime.fromisoformat(sys.argv[1].replace('Z', '+00:00'))
                print(f"Using provided window_start: {window_start.isoformat()}\n")
            except ValueError:
                print(f"[ERROR] Invalid window_start format: {sys.argv[1]}")
                print("Expected ISO 8601 format (e.g., 2024-01-01T00:00:00Z)")
                sys.exit(1)
        
        # Run pipeline
        run_id = run_daily_pipeline(window_start)
        
        print("\n" + "=" * 60)
        print(f"[SUCCESS] Pipeline run completed successfully!")
        print(f"Run ID: {run_id}")
        print("=" * 60)
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n[INFO] Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n[ERROR] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
