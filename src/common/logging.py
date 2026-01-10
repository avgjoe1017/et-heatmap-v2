"""
Logging configuration with Sentry integration.
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(level: str = None, log_file: str = None, enable_sentry: bool = True):
    """
    Setup application logging with console and optional file output.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to LOG_LEVEL env var or INFO.
        log_file: Path to log file. Defaults to logs/app.log. Set to None to disable file logging.
    """
    # Get log level from env or parameter
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    log_level = getattr(logging, level, logging.INFO)
    
    # Create logs directory if needed
    if log_file is None:
        log_file = os.getenv("LOG_FILE", "logs/app.log")
    
    # Format for both console and file
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    handlers = [console_handler]
    
    # File handler (if log_file is not None)
    if log_file and log_file.lower() != "none":
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Rotating file handler (10MB max, 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # Initialize Sentry if enabled and DSN is configured
    if enable_sentry:
        setup_sentry()


def setup_sentry():
    """
    Initialize Sentry error tracking.

    Requires SENTRY_DSN environment variable to be set.
    Optionally set SENTRY_ENVIRONMENT (e.g., production, staging, development).
    """
    sentry_dsn = os.getenv("SENTRY_DSN")

    if not sentry_dsn:
        logging.debug("Sentry DSN not configured. Error tracking disabled.")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        # Get environment and release info
        environment = os.getenv("SENTRY_ENVIRONMENT", "development")
        release = os.getenv("SENTRY_RELEASE", "et-heatmap@0.1.0")

        # Configure Sentry
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            release=release,

            # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
            # In production, reduce this value to reduce load (e.g., 0.1 = 10%)
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),

            # Capture logs as breadcrumbs
            integrations=[
                LoggingIntegration(
                    level=logging.INFO,  # Capture info and above
                    event_level=logging.ERROR  # Send errors as events
                )
            ],

            # Set sample rate for error events (1.0 = 100%)
            sample_rate=1.0,

            # Send default PII (personally identifiable information)
            send_default_pii=False,

            # Attach stack trace to messages
            attach_stacktrace=True,

            # Max breadcrumbs
            max_breadcrumbs=50,
        )

        logging.info(f"Sentry error tracking initialized (environment: {environment})")

    except ImportError:
        logging.warning("sentry-sdk not installed. Install with: pip install sentry-sdk")
    except Exception as e:
        logging.error(f"Failed to initialize Sentry: {e}")