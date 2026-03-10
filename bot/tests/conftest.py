import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


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
