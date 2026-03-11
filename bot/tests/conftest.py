import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class MockPipeline:
    """Mock pipeline for testing."""

    def __init__(self, history_file=None):
        self.media = []
        self._history = set()
        self._history_file = history_file

    def check_post_history(self, fn):
        return fn in self._history

    def add_media(self, media_type, path):
        self.media.append({"type": media_type, "path": path})

    def log(self, msg):
        print(f"[LOG] {msg}")


@pytest.fixture
def temp_history_file(tmp_path):
    """Create a temporary history file."""
    history_file = tmp_path / "test.hist"
    return history_file


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file."""
    log_file = tmp_path / "test.log"
    return log_file


@pytest.fixture
def mock_pipeline():
    """Create a mock pipeline for testing."""
    return MockPipeline()


@pytest.fixture
def temp_download_dir(tmp_path):
    """Create a temporary directory for downloads and change to it."""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_dir)


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up downloaded test files after each test."""
    yield
    extensions = ["*.mp4", "*.jpg", "*.jpeg", "*.png", "*.gif"]
    for ext in extensions:
        for f in Path(".").glob(ext):
            try:
                f.unlink()
            except Exception:
                pass
