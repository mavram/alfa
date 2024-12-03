import os
import time
from tempfile import TemporaryDirectory

import pytest

from alfa.utils import create_directories_for_path, get_current_utc_timestamp


def test_create_directories_for_valid_path():
    with TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "subdir", "file.txt")
        create_directories_for_path(path)
        assert os.path.exists(os.path.dirname(path)), "Directories should be created."


def test_no_action_for_file_only_path():
    path = "file.txt"  # No directory specified
    create_directories_for_path(path)
    # Ensure no directories are created
    assert not os.path.exists(
        os.path.dirname(path)
    ), "No directories should be created for a file-only path."


def test_permission_error():
    # Use a restricted directory to simulate a permission error
    restricted_dir = "/root/restricted/file.txt"  # Likely to fail on most systems
    with pytest.raises(OSError):
        create_directories_for_path(restricted_dir)


def test_existing_directories():
    with TemporaryDirectory() as temp_dir:
        existing_dir = os.path.join(temp_dir, "existing_dir")
        os.makedirs(existing_dir)  # Pre-create the directory
        path = os.path.join(existing_dir, "file.txt")
        create_directories_for_path(path)  # Should not raise any exceptions
        assert os.path.exists(existing_dir), "The existing directory should still exist."


def test_invalid_path():
    invalid_path = "/invalid_path?<>|/file.txt"  # Likely invalid on most systems
    with pytest.raises(OSError):
        create_directories_for_path(invalid_path)


def test_get_current_utc_timestamp():
    # Capture the current time before calling the function
    before = int(time.time())

    # Call the function to get the current UTC timestamp
    timestamp = get_current_utc_timestamp()

    # Capture the current time after calling the function
    after = int(time.time())

    # Assert that the returned timestamp is an integer
    assert isinstance(timestamp, int), f"Expected timestamp to be int, got {type(timestamp).__name__}"

    # Assert that the timestamp is between 'before' and 'after'
    assert before <= timestamp <= after, f"Timestamp {timestamp} is not between {before} and {after}"
