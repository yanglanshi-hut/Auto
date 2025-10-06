"""Logging utilities for the automation project.

Provides `setup_logger(name, log_file)` to standardize logging
configuration across modules without duplicating boilerplate.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Union


def setup_logger(name: str, log_file: Union[str, Path]) -> logging.Logger:
    """Create or retrieve a configured logger.

    - Attaches a StreamHandler to stdout and a FileHandler to `log_file`.
    - Idempotent: repeated calls for the same logger won't add duplicate handlers.
    - Ensures the parent directory for `log_file` exists.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    log_path = Path(log_file)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    # Build a consistent formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # Attach handlers only if not already present
    handler_types = {type(h) for h in logger.handlers}

    if logging.StreamHandler not in handler_types:
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    if logging.FileHandler not in handler_types:
        try:
            fh = logging.FileHandler(str(log_path), encoding='utf-8')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception:
            # If the file cannot be opened, keep stdout handler only.
            pass

    return logger
