"""
🛡️ Rate Limiter
================
Prevents spam and abuse.
Default: max 10 actions per user per 60 seconds.
"""

import time
from collections import defaultdict

# user_id → list of timestamps
_requests: dict[int, list] = defaultdict(list)

# Config
MAX_REQUESTS = 10   # max actions
WINDOW_SEC   = 60   # per N seconds


def is_rate_limited(user_id: int) -> bool:
    """
    Returns True if the user has exceeded the rate limit.
    Automatically cleans up old timestamps.
    """
    now  = time.time()
    reqs = _requests[user_id]

    # Remove timestamps outside the window
    _requests[user_id] = [t for t in reqs if now - t < WINDOW_SEC]

    if len(_requests[user_id]) >= MAX_REQUESTS:
        return True

    _requests[user_id].append(now)
    return False


def reset_user(user_id: int):
    """Reset rate limit for a specific user (admin use)."""
    _requests.pop(user_id, None)
