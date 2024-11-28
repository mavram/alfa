import os
from tempfile import TemporaryDirectory

import pytest

from alfa.util import create_directories_for_path


def test_create_directories_for_valid_path():
    """Test that directories are created for a valid path."""
    with TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "subdir", "file.txt")
        create_directories_for_path(path)
        assert os.path.exists(os.path.dirname(path)), "Directories should be created."


def test_no_action_for_file_only_path():
    """Test that no directories are created when the path is just a file name."""
    path = "file.txt"  # No directory specified
    create_directories_for_path(path)
    # Ensure no directories are created
    assert not os.path.exists(
        os.path.dirname(path)
    ), "No directories should be created for a file-only path."


def test_permission_error():
    """Test that an exception is raised when permissions are insufficient."""
    # Use a restricted directory to simulate a permission error
    restricted_dir = "/root/restricted/file.txt"  # Likely to fail on most systems
    with pytest.raises(OSError):
        create_directories_for_path(restricted_dir)


def test_existing_directories():
    """Test that no error occurs when directories already exist."""
    with TemporaryDirectory() as temp_dir:
        existing_dir = os.path.join(temp_dir, "existing_dir")
        os.makedirs(existing_dir)  # Pre-create the directory
        path = os.path.join(existing_dir, "file.txt")
        create_directories_for_path(path)  # Should not raise any exceptions
        assert os.path.exists(existing_dir), "The existing directory should still exist."


def test_invalid_path():
    """Test that an exception is raised for invalid paths."""
    invalid_path = "/invalid_path?<>|/file.txt"  # Likely invalid on most systems
    with pytest.raises(OSError):
        create_directories_for_path(invalid_path)
