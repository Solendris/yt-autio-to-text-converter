"""
Time formatting utilities.
"""


def format_seconds(seconds: float) -> str:
    """
    Convert seconds to [MM:SS] or [HH:MM:SS] format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"
    else:
        return f"[{minutes:02d}:{secs:02d}]"
