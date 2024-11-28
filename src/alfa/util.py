import os


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
