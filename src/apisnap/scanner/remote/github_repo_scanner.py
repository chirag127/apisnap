"""GitHub repository scanner - handles GitHub-as-database pattern."""

import json
import re
import urllib.parse
from pathlib import Path
from typing import Optional
import httpx

import yaml

from apisnap.schema import RouteManifest, Route, Param
from apisnap.scanner.base import BaseScanner
from apisnap.scanner.schema_inferrer import SchemaInferrer


GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

JSON_FILE_PATTERNS = [
    "data/",
    "public/",
    "api/",
    "dist/",
    "output/",
    "assets/",
    "_data/",
    "json/",
]

GENERATOR_PATTERNS = [
    ".github/workflows/",
    "scripts/",
    "fetch_",
    "update_",
    "sync_",
]


class GitHubRepoScanner(BaseScanner):
    """Scanner for GitHub repos that use GitHub as a database."""

    def __init__(self):
        self.inferrer = SchemaInferrer()
        self.http_client = httpx.Client(timeout=30.0)

    def can_handle(self, path: str) -> bool:
        """Check if path is a GitHub repository URL."""
        path_lower = path.lower()
        return "github.com" in path_lower or "/" in path_lower

    def scan(self, url: str, **kwargs) -> RouteManifest:
        """Scan a GitHub repository for JSON data files.

        Steps:
        1. Parse owner/repo from URL
        2. Fetch repo tree from GitHub API
        3. Find and parse workflow YAML files
        4. Find and fetch JSON data files
        5. Detect public serving URL
        6. Build RouteManifest
        """
        # Parse owner/repo from URL
        owner, repo = self._parse_github_url(url)

        if not owner or not repo:
            return RouteManifest(
                source_mode="github",
                detected_at=url,
            )

        # Fetch repo tree
        tree = self._fetch_repo_tree(owner, repo)

        if not tree:
            return RouteManifest(
                source_mode="github",
                detected_at=url,
            )

        # Find workflow files and parse cron schedules
        workflow_info = self._parse_workflows(owner, repo, tree)

        # Find JSON data files
        json_files = self._find_json_data_files(tree)

        # Detect public serving URL
        base_url = self._detect_public_url(owner, repo, tree)

        if not base_url:
            base_url = f"https://{owner}.github.io/{repo}"

        # Build routes for each JSON file
        routes = []
        for json_path in json_files:
            try:
                content = self._fetch_file_content(owner, repo, json_path)
                if content:
                    route = self._build_route(
                        json_path,
                        content,
                        base_url,
                        workflow_info.get(json_path),
                    )
                    routes.append(route)
            except Exception:
                continue

        return RouteManifest(
            routes=routes,
            base_url=base_url,
            framework="github-data-repo",
            project_name=f"{owner}/{repo}",
            source_mode="github",
            detected_at=url,
        )

    def _parse_github_url(self, url: str) -> tuple[str, str]:
        """Parse owner and repo from GitHub URL.

        Handles:
        - https://github.com/owner/repo
        - https://github.com/owner/repo/
        - github.com/owner/repo
        - owner/repo
        """
        # Clean URL
        url = url.strip().rstrip("/")

        # Remove https:// or http://
        if url.startswith("https://"):
            url = url[8:]
        elif url.startswith("http://"):
            url = url[7:]

        # Remove github.com/
        if url.startswith("github.com/"):
            url = url[11:]

        # Split by /
        parts = url.split("/")

        if len(parts) >= 2:
            return parts[0], parts[1]

        return "", ""

    def _fetch_repo_tree(self, owner: str, repo: str) -> list[dict]:
        """Fetch repository tree from GitHub API.

        Returns list of {path, type, url} for all files.
        """
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/main?recursive=1"

        try:
            response = self.http_client.get(url)
            response.raise_for_status()
            data = response.json()

            return data.get("tree", [])
        except Exception:
            # Try with 'master' branch
            url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/master?recursive=1"
            try:
                response = self.http_client.get(url)
                response.raise_for_status()
                data = response.json()
                return data.get("tree", [])
            except Exception:
                return []

    def _parse_workflows(self, owner: str, repo: str, tree: list[dict]) -> dict:
        """Parse workflow files to extract cron schedules.

        Returns dict mapping output file path to workflow info.
        """
        workflow_info = {}

        # Find workflow files
        workflow_files = [
            item
            for item in tree
            if item.get("type") == "blob"
            and item.get("path", "").startswith(".github/workflows/")
            and item.get("path", "").endswith((".yml", ".yaml"))
        ]

        for workflow in workflow_files:
            path = workflow.get("path", "")
            try:
                content = self._fetch_file_content(owner, repo, path)
                if content:
                    info = self._parse_workflow_content(content)
                    # Map output files to workflow info
                    for output_file in info.get("output_files", []):
                        workflow_info[output_file] = info
            except Exception:
                continue

        return workflow_info

    def _parse_workflow_content(self, content: str) -> dict:
        """Parse workflow YAML content."""
        try:
            workflow = yaml.safe_load(content)

            cron_schedule = None
            output_files = []

            # Extract cron schedule - handle both "on" and True (YAML boolean)
            # YAML parses "on:" as boolean True
            on_config = workflow.get("on") or workflow.get(True)
            if on_config:
                if isinstance(on_config, dict):
                    if "schedule" in on_config:
                        schedules = on_config["schedule"]
                        if isinstance(schedules, list) and schedules:
                            cron = schedules[0].get("cron", "")
                            # Handle YAML single-quoted strings which preserve quotes
                            if cron and cron.startswith("'") and cron.endswith("'"):
                                cron = cron[1:-1]
                            cron_schedule = cron
                        elif isinstance(schedules, dict):
                            cron_schedule = schedules.get("cron", "")

                    # Extract repository dispatch triggers
                    if "repository_dispatch" in on_config:
                        output_files.append("repository dispatch")

            # Find file operations (checkout, write-file)
            jobs = workflow.get("jobs", {})
            for job_name, job in jobs.items():
                steps = job.get("steps", [])
                for step in steps:
                    uses = step.get("uses", "")
                    if "checkout" in uses:
                        continue
                    if "write-file" in uses:
                        # Try to extract output path
                        with_config = step.get("with", {})
                        if "path" in with_config:
                            output_files.append(with_config["path"])

                    # Check run commands for curl/fetch
                    run = step.get("run", "")
                    if "curl" in run or "fetch" in run or "requests" in run:
                        # Try to extract output
                        output_match = re.search(r'-o\s+["\']?([^"\'\s]+)["\']?', run)
                        if output_match:
                            output_files.append(output_match.group(1))

            return {
                "cron_schedule": cron_schedule,
                "output_files": output_files,
            }
        except Exception:
            return {"cron_schedule": None, "output_files": []}

    def _find_json_data_files(self, tree: list[dict]) -> list[str]:
        """Find JSON data files in tree."""
        json_files = []

        for item in tree:
            if item.get("type") != "blob":
                continue

            path = item.get("path", "")

            # Check if it's a JSON file
            if not path.endswith(".json"):
                continue

            # Check if it's in a data directory
            for pattern in JSON_FILE_PATTERNS:
                if pattern in path:
                    json_files.append(path)
                    break

        return json_files

    def _fetch_file_content(self, owner: str, repo: str, path: str) -> str:
        """Fetch raw file content from GitHub."""
        url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/main/{path}"

        try:
            response = self.http_client.get(url)
            response.raise_for_status()
            return response.text
        except Exception:
            # Try with master branch
            url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/master/{path}"
            try:
                response = self.http_client.get(url)
                response.raise_for_status()
                return response.text
            except Exception:
                return ""

    def _detect_public_url(
        self, owner: str, repo: str, tree: list[dict]
    ) -> Optional[str]:
        """Detect public serving URL.

        Checks for:
        - CNAME file (custom domain)
        - wrangler.toml (Cloudflare Pages)
        - docs/ folder (GitHub Pages)
        """
        # Check for CNAME file
        cname_file = next((item for item in tree if item.get("path") == "CNAME"), None)
        if cname_file:
            try:
                content = self._fetch_file_content(owner, repo, "CNAME")
                if content:
                    domain = content.strip()
                    if domain:
                        return f"https://{domain}"
            except Exception:
                pass

        # Check for wrangler.toml (Cloudflare Pages)
        wrangler = next(
            (item for item in tree if item.get("path") == "wrangler.toml"), None
        )
        if wrangler:
            # Try to extract project name
            try:
                content = self._fetch_file_content(owner, repo, "wrangler.toml")
                if content:
                    # Simple parse for name
                    match = re.search(r'name\s*=\s*"([^"]+)"', content)
                    if match:
                        project_name = match.group(1)
                        return f"https://{project_name}.pages.dev"
            except Exception:
                pass

        # Check for .cloudflare directory
        cloudflare_dir = any(
            item.get("path", "").startswith(".cloudflare/") for item in tree
        )
        if cloudflare_dir:
            return f"https://{repo}.pages.dev"

        # Check for docs/ folder (GitHub Pages from docs/)
        docs_folder = any(item.get("path", "").startswith("docs/") for item in tree)
        if docs_folder:
            return f"https://{owner}.github.io/{repo}/docs"

        return None

    def _build_route(
        self,
        json_path: str,
        content: str,
        base_url: str,
        workflow_info: Optional[dict],
    ) -> Route:
        """Build a Route from JSON file content."""
        try:
            data = json.loads(content)
        except Exception:
            data = {}

        # Infer schema
        response_schema = self.inferrer.infer(data)

        # Build public URL
        public_url = (
            f"{base_url}/{json_path}"
            if not base_url.endswith("/")
            else f"{base_url}{json_path}"
        )

        # Get refresh schedule from workflow
        refresh_schedule = None
        if workflow_info:
            refresh_schedule = workflow_info.get("cron_schedule")

        return Route(
            method="GET",
            path=f"/{json_path}",
            response_schema=response_schema,
            auth_required=False,
            source="github-data-repo",
            confidence=0.95,
            refresh_schedule=refresh_schedule,
            public_url=public_url,
            summary=f"JSON data file: {json_path}",
        )
