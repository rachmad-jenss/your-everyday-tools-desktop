"""Shared helpers for input validation and error handling.

These centralize patterns that were previously duplicated (and often missing)
across the route blueprints: bounds-checked numeric form values, sanitized
error responses that don't leak internals to the client, and consistent
"no file uploaded" messages.
"""

from __future__ import annotations

import logging
from typing import Optional

from flask import current_app

logger = logging.getLogger(__name__)


def safe_int(value, default: int, min_val: Optional[int] = None,
             max_val: Optional[int] = None) -> int:
    """Parse a form value to int, clamp to bounds, fall back to default.

    Never raises. Treats None, empty string, and unparseable input as default.
    """
    if value is None or value == "":
        result = default
    else:
        try:
            result = int(float(str(value).strip()))
        except (TypeError, ValueError):
            result = default
    if min_val is not None and result < min_val:
        result = min_val
    if max_val is not None and result > max_val:
        result = max_val
    return result


def safe_float(value, default: float, min_val: Optional[float] = None,
               max_val: Optional[float] = None) -> float:
    """Parse a form value to float, clamp to bounds, fall back to default."""
    if value is None or value == "":
        result = default
    else:
        try:
            result = float(str(value).strip())
        except (TypeError, ValueError):
            result = default
    if min_val is not None and result < min_val:
        result = min_val
    if max_val is not None and result > max_val:
        result = max_val
    return result


def log_error(exc: BaseException, context: str = "") -> None:
    """Log an exception with full traceback to the app logger.

    Use this together with returning a sanitized friendly message to the user.
    """
    try:
        current_app.logger.exception("%s: %s", context or "unhandled", exc)
    except RuntimeError:
        logger.exception("%s: %s", context or "unhandled", exc)


NO_FILE_SINGLE = "Please upload a file."
NO_FILE_MULTIPLE = "Please upload at least one file."
