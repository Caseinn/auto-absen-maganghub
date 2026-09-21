"""Telegram notification helper."""

import requests

from app.api.client import TIMEOUT
from app.config import settings
from app.utils.log import log


def notify(text: str) -> None:
    """Send a Telegram message if bot credentials are set.

    Does nothing when credentials are missing, and never raises,
    so a notification failure cannot break the attendance flow.

    Args:
        text: Message text to send.
    """
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id
    if not token or not chat_id:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=TIMEOUT,
        )
    except Exception as e:
        log(f"[WARN] Notifikasi Telegram gagal: {e}")
