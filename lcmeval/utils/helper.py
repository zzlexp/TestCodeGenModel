import datetime


def timestamp() -> str:
    """Returns a timestamp string in the format of "%Y%m%d%H%M%S"."""
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")
