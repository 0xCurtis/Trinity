import time
from pathlib import Path

import pytest
import requests

from src.maker.reddit_maker import reddit


class TestReddit:
    """Tests for Reddit maker."""

    def test_reddit_with_image(self, mock_pipeline, temp_download_dir):
        """Test fetching a post with image from Reddit."""
        args = {
            "reddit": {"subreddit": "pics", "sort": "hot", "limit": 10, "time_filter": "day"},
            "unique_posts": False,
        }

        result = reddit(mock_pipeline, args)

        assert result is not None
        assert "string" in result
        assert len(mock_pipeline.media) > 0

        media = mock_pipeline.media[0]
        assert media["type"] in ["photo", "animation"]

        media_files = (
            list(Path(".").glob("*.jpg"))
            + list(Path(".").glob("*.jpeg"))
            + list(Path(".").glob("*.png"))
            + list(Path(".").glob("*.gif"))
        )
        assert len(media_files) > 0, "No image file was downloaded"

    def test_reddit_text_only(self, mock_pipeline, temp_download_dir):
        """Test fetching a text-only post from Reddit."""
        args = {
            "reddit": {"subreddit": "askreddit", "sort": "hot", "limit": 10, "time_filter": "day"},
            "unique_posts": False,
        }

        result = reddit(mock_pipeline, args)

        assert result is not None
        assert "string" in result

        media_files = (
            list(Path(".").glob("*.jpg"))
            + list(Path(".").glob("*.jpeg"))
            + list(Path(".").glob("*.png"))
            + list(Path(".").glob("*.gif"))
        )

        if len(media_files) > 0:
            assert mock_pipeline.media[0]["type"] == "photo"
        else:
            assert len(mock_pipeline.media) == 0
