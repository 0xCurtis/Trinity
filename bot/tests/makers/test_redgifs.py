import glob
from pathlib import Path

import pytest

from src.maker.redgifs_maker import redgifs, close_api


class TestRedgifs:
    """Tests for RedGifs maker."""

    @pytest.fixture(autouse=True)
    def close_api_after(self):
        """Close API after each test."""
        yield
        close_api()

    def test_redgifs_video(self, mock_pipeline, temp_download_dir):
        """Test fetching a video from RedGifs."""
        args = {
            "type": "video",
            "redgifs": {"tags": "women", "sort": "trending"},
            "unique_posts": False,
        }

        result = redgifs(mock_pipeline, args)

        assert result is not None
        assert len(mock_pipeline.media) > 0
        assert mock_pipeline.media[0]["type"] == "video"

        media_files = list(Path(".").glob("*.mp4"))
        assert len(media_files) > 0, "No video file was downloaded"

    def test_redgifs_gif(self, mock_pipeline, temp_download_dir):
        """Test fetching a GIF from RedGifs."""
        args = {
            "type": "animation",
            "redgifs": {"tags": "teen", "sort": "trending"},
            "unique_posts": False,
        }

        result = redgifs(mock_pipeline, args)

        assert result is not None
        assert len(mock_pipeline.media) > 0

        media_files = list(Path(".").glob("*.gif")) + list(Path(".").glob("*.mp4"))
        assert len(media_files) > 0, "No GIF/video file was downloaded"
