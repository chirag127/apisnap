"""Tests for GitHub repo scanner."""

import pytest
import json

from apisnap.scanner.remote.github_repo_scanner import GitHubRepoScanner
from apisnap.schema import RouteManifest


class TestGitHubRepoScanner:
    """Tests for GitHubRepoScanner."""

    def test_can_handle(self):
        """Test can_handle detects GitHub URLs."""
        scanner = GitHubRepoScanner()

        assert scanner.can_handle("https://github.com/user/repo") is True
        assert scanner.can_handle("github.com/user/repo") is True
        assert scanner.can_handle("user/repo") is True

    def test_parse_github_url(self):
        """Test parsing GitHub URL to owner/repo."""
        scanner = GitHubRepoScanner()

        owner, repo = scanner._parse_github_url("https://github.com/user/repo")
        assert owner == "user"
        assert repo == "repo"

        owner, repo = scanner._parse_github_url("github.com/user/repo/")
        assert owner == "user"
        assert repo == "repo"

        owner, repo = scanner._parse_github_url("user/repo")
        assert owner == "user"
        assert repo == "repo"

    def test_parse_workflow_content(self):
        """Test parsing workflow YAML."""
        scanner = GitHubRepoScanner()

        content = """
name: Update Data
on:
  schedule:
    - cron: '0 */6 * * *'
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python fetch.py
"""

        info = scanner._parse_workflow_content(content)

        assert info["cron_schedule"] == "0 */6 * * *"

    def test_build_route(self):
        """Test building route from JSON file."""
        scanner = GitHubRepoScanner()

        json_content = json.dumps({"users": [{"id": 1, "name": "John"}]})

        route = scanner._build_route(
            "data/users.json",
            json_content,
            "https://user.github.io/repo",
            None,
        )

        assert route.method == "GET"
        assert "/data/users.json" in route.path
        assert route.source == "github-data-repo"
        assert route.confidence == 0.95
        assert route.public_url == "https://user.github.io/repo/data/users.json"
