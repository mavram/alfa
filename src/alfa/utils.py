import os


def create_directories_for_path(path):
    # Extract the directory portion of the path
    directory = os.path.dirname(path)
    # Create directories if they are missing
    if directory:  # Avoid creating root directory if path is just a file name
        os.makedirs(directory, exist_ok=True)
