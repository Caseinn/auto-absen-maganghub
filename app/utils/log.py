"""Dual console-and-file logging."""

from pathlib import Path

from app.utils.time import now_wib

LOG_FILE = Path(__file__).parent.parent.parent / "absen.log"


def log(msg: str) -> None:
    """Print a message and append it to the log file with a timestamp.

    Never raises, so logging cannot break the attendance flow.

    Args:
        msg: Message text.
    """
    print(msg)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{now_wib().strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")
    except OSError:
        pass
