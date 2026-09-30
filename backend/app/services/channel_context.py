"""
Extract channel identity from request headers (used by bots).
"""
from typing import Optional, Tuple

from fastapi import Request


CHANNEL_HEADER = "X-ArthSathi-Channel"
USER_HEADER = "X-ArthSathi-User-Id"


def get_channel_context(request: Request) -> Tuple[Optional[str], Optional[str]]:
    channel = request.headers.get(CHANNEL_HEADER)
    user_id = request.headers.get(USER_HEADER)
    if channel and user_id:
        return channel.strip().lower(), user_id.strip()
    return None, None
