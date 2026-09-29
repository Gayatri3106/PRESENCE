"""
Room code generation and validation.

A room code is a short, human-readable alphanumeric string
that expires after a configurable TTL (default 2 minutes).
"""

import random
import string
from datetime import datetime, timedelta, timezone

from config import config


def generate_room_code(length: int | None = None) -> str:
    """
    Generate a random alphanumeric room code.

    We exclude ambiguous characters (0/O, 1/I/L) for readability
    when displayed on a projector in a classroom.
    """
    if length is None:
        length = config.ROOM_CODE_LENGTH

    # Safe alphabet — no look-alikes
    safe_chars = string.ascii_uppercase.replace("O", "").replace("I", "").replace("L", "")
    safe_digits = string.digits.replace("0", "").replace("1", "")
    pool = safe_chars + safe_digits

    code = "".join(random.choices(pool, k=length))
    return code


def compute_expiry(ttl_seconds: int | None = None) -> datetime:
    """Return the UTC expiry timestamp for a newly generated code."""
    if ttl_seconds is None:
        ttl_seconds = config.ROOM_CODE_TTL_SECONDS
    return datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)


def is_expired(expires_at: datetime) -> bool:
    """Check whether a session's expiry time has passed."""
    now = datetime.now(timezone.utc)
    # Handle both aware and naive datetimes
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return now > expires_at

