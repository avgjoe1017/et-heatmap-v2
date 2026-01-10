"""
Start the FastAPI server with proper configuration.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Validate configuration before starting
from scripts.validate_config import validate_config


def main():
    """Entry point for script execution."""
    print("ET Heatmap API Server\n")
    
    # Validate configuration
    if not validate_config():
        print("\n[ERROR] Configuration validation failed. Please fix errors before starting the server.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Starting API server...")
    print("=" * 60 + "\n")
    
    # Import after validation
    import uvicorn
    from src.app.main import app
    
    # Get configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"Server will start at: http://{host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"Debug Mode: {reload}\n")
    
    # Start server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )


if __name__ == "__main__":
    main()
