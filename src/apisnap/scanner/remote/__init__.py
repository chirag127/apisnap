"""Remote scanners for URLs."""

from apisnap.scanner.remote.openapi_scanner import OpenAPIScanner
from apisnap.scanner.remote.json_scanner import JSONScanner
from apisnap.scanner.remote.crawl_scanner import CrawlScanner
from apisnap.scanner.remote.github_repo_scanner import GitHubRepoScanner

__all__ = [
    "OpenAPIScanner",
    "JSONScanner",
    "CrawlScanner",
    "GitHubRepoScanner",
]
