import pytest

from src.maker.string_maker import string


class TestString:
    """Tests for String maker."""

    def test_string_maker(self, mock_pipeline):
        """Test that string maker returns args unchanged."""
        args = {"string": {"text": "Hello, World!"}}

        result = string(mock_pipeline, args)

        assert result is not None
        assert result == args
        assert result["string"]["text"] == "Hello, World!"
        assert len(mock_pipeline.media) == 0
