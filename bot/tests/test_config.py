import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.config import _resolve_string, resolve_secrets


class TestConfigResolution:
    def test_resolve_string_with_env_var(self):
        with patch.dict("os.environ", {"TEST_VAR": "test_value"}):
            result = _resolve_string("${TEST_VAR}")
            assert result == "test_value"

    def test_resolve_string_without_env_var_raises(self):
        with pytest.raises(ValueError, match="not set"):
            _resolve_string("${NONEXISTENT_VAR_12345}")

    def test_resolve_dict(self):
        with patch.dict("os.environ", {"TELEGRAM_TOKEN": "abc123"}):
            result = resolve_secrets({"token": "${TELEGRAM_TOKEN}"})
            assert result == {"token": "abc123"}

    def test_resolve_nested_dict(self):
        with patch.dict("os.environ", {"TOKEN": "secret"}):
            result = resolve_secrets({"auth": {"telegram": {"token": "${TOKEN}"}}})
            assert result == {"auth": {"telegram": {"token": "secret"}}}

    def test_resolve_list(self):
        with patch.dict("os.environ", {"VAR": "value"}):
            result = resolve_secrets(["${VAR}", "static"])
            assert result == ["value", "static"]

    def test_resolve_mixed(self):
        with patch.dict("os.environ", {"VAR1": "val1", "VAR2": "val2"}):
            result = resolve_secrets(
                {"a": "${VAR1}", "b": 123, "c": ["${VAR2}", "static"], "d": {"e": "${VAR1}"}}
            )
            assert result == {"a": "val1", "b": 123, "c": ["val2", "static"], "d": {"e": "val1"}}

    def test_no_replacement_needed(self):
        result = _resolve_string("plain_string")
        assert result == "plain_string"

    def test_multiple_vars_in_string(self):
        with patch.dict("os.environ", {"VAR1": "a", "VAR2": "b"}):
            result = _resolve_string("${VAR1}-${VAR2}")
            assert result == "a-b"
