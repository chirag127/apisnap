"""HTTP client utilities."""

import httpx
from typing import Optional


_http_client: Optional[httpx.Client] = None


def get_http_client() -> httpx.Client:
    """Get singleton HTTP client with retry logic."""
    global _http_client

    if _http_client is None:
        _http_client = httpx.Client(
            timeout=30.0,
            retry=3,
        )

    return _http_client


def close_http_client() -> None:
    """Close the HTTP client."""
    global _http_client

    if _http_client is not None:
        _http_client.close()
        _http_client = None
