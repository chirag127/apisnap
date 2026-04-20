"""Tests for scanner detector."""

import pytest

from apisnap.scanner.detector import detect_scanner, detect_and_scan


class TestDetectScanner:
    """Tests for detect_scanner function."""

    def test_detect_scanner_with_url(self):
        """Test detecting scanner for URL."""
        scanner = detect_scanner("https://api.example.com/openapi.json")
        assert scanner is not None

    def test_detect_scanner_with_github(self):
        """Test detecting scanner for GitHub URL."""
        scanner = detect_scanner("https://github.com/user/repo")
        assert scanner is not None


class TestDetectAndScan:
    """Tests for detect_and_scan function."""

    def test_detect_and_scan_local_path(self):
        """Test scanning local path."""
        manifest = detect_and_scan(".")
        assert manifest is not None
        assert manifest.source_mode is not None

    def test_detect_and_scan_url(self):
        """Test scanning URL."""
        manifest = detect_and_scan("https://example.com")
        assert manifest is not None
