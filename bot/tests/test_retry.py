import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import requests

from src.retry import is_retriable_error, retry_with_backoff


class TestRetryDecorator:
    def test_succeeds_on_first_attempt(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "success"

        result = succeed()
        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.ConnectionError("Connection failed")
            return "success"

        result = fail_twice()
        assert result == "success"
        assert call_count == 3

    def test_raises_after_max_retries(self):
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.1)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise requests.ConnectionError("Connection failed")

        with pytest.raises(requests.ConnectionError):
            always_fail()
        assert call_count == 3

    def test_retries_on_specific_exceptions(self):
        call_count = 0

        @retry_with_backoff(
            max_retries=2, base_delay=0.1, retriable_exceptions=(ValueError, TypeError)
        )
        def raise_value_error():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("test")
            return "success"

        result = raise_value_error()
        assert result == "success"

    def test_does_not_retry_non_retriable_exceptions(self):
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("test")

        with pytest.raises(TypeError):
            raise_type_error()
        assert call_count == 1


class TestIsRetriableError:
    def test_429_is_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 429
        assert is_retriable_error(response) is True

    def test_500_is_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 500
        assert is_retriable_error(response) is True

    def test_502_is_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 502
        assert is_retriable_error(response) is True

    def test_503_is_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 503
        assert is_retriable_error(response) is True

    def test_504_is_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 504
        assert is_retriable_error(response) is True

    def test_200_is_not_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        assert is_retriable_error(response) is False

    def test_400_is_not_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 400
        assert is_retriable_error(response) is False

    def test_404_is_not_retriable(self):
        response = MagicMock(spec=requests.Response)
        response.status_code = 404
        assert is_retriable_error(response) is False
