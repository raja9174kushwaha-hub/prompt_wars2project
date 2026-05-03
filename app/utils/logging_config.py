"""
Centralised logging configuration with Google Cloud Logging integration.

On Cloud Run, automatically uses Google Cloud Logging for structured,
searchable logs in the GCP Console. Falls back to standard stdout
logging in local development.
"""

import logging
import os
import sys


def _setup_cloud_logging() -> bool:
    """
    Attempt to initialise Google Cloud Logging.

    Returns:
        True if Cloud Logging is configured, False otherwise.
    """
    try:
        import google.cloud.logging as cloud_logging

        client = cloud_logging.Client()
        client.setup_logging(log_level=logging.INFO)
        logging.getLogger(__name__).info(
            "Google Cloud Logging initialised successfully."
        )
        return True
    except ImportError:
        return False
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Cloud Logging unavailable (%s), using stdout.", exc
        )
        return False


def setup_logging() -> None:
    """
    Configure application logging.

    Strategy:
      1. If running on Cloud Run (ENABLE_CLOUD_LOGGING=true) and
         google-cloud-logging is installed, use structured Cloud Logging.
      2. Otherwise, fall back to stdout with a human-readable format.
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    enable_cloud = os.getenv("ENABLE_CLOUD_LOGGING", "true").lower() == "true"

    cloud_configured = False
    if enable_cloud:
        cloud_configured = _setup_cloud_logging()

    if not cloud_configured:
        logging.basicConfig(
            level=numeric_level,
            format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
            stream=sys.stdout,
            force=True,
        )

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("grpc").setLevel(logging.WARNING)
