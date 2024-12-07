import os
from datetime import datetime, timezone


def create_directories_for_path(path):
    """
    Create all missing directories in the given path, assuming it ends with a file name.

    :param path: The file path for which directories need to be created.
    :raises OSError: If there is an error creating the directories (e.g., permissions issue).
    """
    # Extract the directory portion of the path
    directory = os.path.dirname(path)

    # Create directories if they are missing
    if directory:  # Avoid creating root directory if path is just a file name
        os.makedirs(directory, exist_ok=True)


def get_current_utc_timestamp():
    """
    Returns the current UTC timestamp as integer.

    Returns:
        int: The number of seconds since the Unix Epoch (January 1, 1970) in UTC.
    """
    return int(datetime.now(timezone.utc).timestamp())


def get_current_utc_date():
    """
    Get the current date in UTC.

    This method retrieves the current date based on Coordinated Universal Time (UTC).
    It ensures that the returned date is not influenced by the local system timezone.

    Returns:
        datetime.date: The current date in UTC.
    """
    return datetime.now(timezone.utc).date()


def get_timestamp_as_str(timestamp):
    """
    Returns the string representation of given Unix timestamp in UTC

    Returns:
        str: UTC string representation of given unix timestamp
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def get_date_from_timestamp(timestamp):
    """
    Convert an epoch timestamp to a date in UTC.

    This function takes an epoch timestamp (seconds since 1970-01-01 00:00:00 UTC)
    and converts it into a date object in UTC.

    Args:
        epoch_timestamp (int or float): The epoch timestamp to convert.

    Returns:
        datetime.date: The corresponding date in UTC.
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()
