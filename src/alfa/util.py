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
    Returns the current UTC timestamp as an integer.

    Returns:
        int: The number of seconds since the Unix Epoch (January 1, 1970) in UTC.
    """
    return int(datetime.now(timezone.utc).timestamp())
