"""WIB (UTC+7) time utilities."""

from datetime import datetime, timezone, timedelta

WIB = timezone(timedelta(hours=7))


def now_wib() -> datetime:
    """Return current datetime in WIB timezone.

    Returns:
        Datetime with WIB timezone.
    """
    return datetime.now(WIB)


def today_str() -> str:
    """Return today's date as YYYY-MM-DD.

    Returns:
        Date string.
    """
    return date_str()


def date_str(days_ago: int = 0) -> str:
    """Return the date N days ago as YYYY-MM-DD.

    Args:
        days_ago: How many days back. 0 means today.

    Returns:
        Date string.
    """
    return (now_wib() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
