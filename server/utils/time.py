"""
utils time.py

Helper function for working with time values.

Contains small, reusable, stateless functions with no business logic or database access.
"""

def format_duration(seconds: int):
    """
    Convert a duration in seconds to a formatted string.

    Args:
        seconds (int): The duration in seconds.

    Returns:
        str: The duration formatted as 'Xh Ym Zs'.
    """
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"