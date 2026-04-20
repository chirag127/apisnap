"""Tests for AI client."""

import pytest
from unittest.mock import patch, MagicMock

from apisnap.ai.client import CerebrasClient
from apisnap.schema import Route


class TestCerebrasClient:
    """Tests for CerebrasClient."""

    @patch("openai.OpenAI")
    def test_client_initialization(self, mock_openai):
        """Test client initialization."""
        client = CerebrasClient("test-key")

        assert client.model == "gpt-oss-120b"

    @patch("openai.OpenAI")
    def test_generate_tests(self, mock_openai):
        """Test test generation."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="test code"))]
        mock_client.chat.completions.create.return_value = mock_response

        client = CerebrasClient("test-key")
        route = Route(
            method="GET",
            path="/api/users",
            response_schema={"type": "object"},
        )

        result = client.generate_tests(route, "pytest")

        assert result == "test code"
        assert mock_client.chat.completions.create.called

    @patch("openai.OpenAI")
    def test_refine_schema(self, mock_openai):
        """Test schema refinement."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"type": "object"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        client = CerebrasClient("test-key")

        result = client.refine_schema({"name": "test"})

        # Result will be JSON parsed
        assert mock_client.chat.completions.create.called
