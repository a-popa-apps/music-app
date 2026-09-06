from __future__ import annotations

import pytest
from fastapi import HTTPException

from app import rate_limit


class _FakeClient:
    def __init__(self, host: str):
        self.host = host


class _FakeRequest:
    def __init__(self, host: str = "1.2.3.4", forwarded_for: str | None = None):
        self.client = _FakeClient(host)
        self.headers = {"x-forwarded-for": forwarded_for} if forwarded_for else {}


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    rate_limit._requests.clear()
    yield
    rate_limit._requests.clear()


def test_allows_requests_under_limit():
    request = _FakeRequest(host="10.0.0.1")
    for _ in range(rate_limit.MAX_REQUESTS_FREE):
        rate_limit.enforce_rate_limit(request)  # should not raise


def test_blocks_requests_over_limit():
    request = _FakeRequest(host="10.0.0.2")
    for _ in range(rate_limit.MAX_REQUESTS_FREE):
        rate_limit.enforce_rate_limit(request)

    with pytest.raises(HTTPException) as exc_info:
        rate_limit.enforce_rate_limit(request)
    assert exc_info.value.status_code == 429


def test_different_ips_tracked_separately():
    request_a = _FakeRequest(host="10.0.0.3")
    request_b = _FakeRequest(host="10.0.0.4")
    for _ in range(rate_limit.MAX_REQUESTS_FREE):
        rate_limit.enforce_rate_limit(request_a)

    rate_limit.enforce_rate_limit(request_b)  # should not raise -- separate bucket


def test_uses_x_forwarded_for_when_present():
    request = _FakeRequest(host="10.0.0.5", forwarded_for="203.0.113.9, 10.0.0.5")
    rate_limit.enforce_rate_limit(request)
    assert "203.0.113.9" in rate_limit._requests
    assert "10.0.0.5" not in rate_limit._requests


def test_key_overrides_ip_and_gets_its_own_bucket():
    request = _FakeRequest(host="10.0.0.6")
    rate_limit.enforce_rate_limit(request, key="uid-123")
    assert "uid-123" in rate_limit._requests
    assert "10.0.0.6" not in rate_limit._requests


def test_two_accounts_behind_the_same_ip_get_separate_buckets():
    request = _FakeRequest(host="10.0.0.7")
    for _ in range(rate_limit.MAX_REQUESTS_FREE):
        rate_limit.enforce_rate_limit(request, key="uid-a")

    rate_limit.enforce_rate_limit(request, key="uid-b")  # should not raise


def test_max_requests_override_allows_a_higher_ceiling_for_pro():
    request = _FakeRequest(host="10.0.0.8")
    for _ in range(rate_limit.MAX_REQUESTS_PRO):
        rate_limit.enforce_rate_limit(
            request, key="uid-pro", max_requests=rate_limit.MAX_REQUESTS_PRO
        )  # should not raise, well past the Free ceiling

    with pytest.raises(HTTPException):
        rate_limit.enforce_rate_limit(
            request, key="uid-pro", max_requests=rate_limit.MAX_REQUESTS_PRO
        )
