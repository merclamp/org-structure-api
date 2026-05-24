"""Logging configuration.

A single place to set up the root logger so that every module can simply
do `logging.getLogger(__name__)` and get consistent, structured output.
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Configure the root logger for the application."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Keep uvicorn's per-request access log from being too noisy.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
