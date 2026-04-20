"""Cerebras AI client for test generation."""

import json
from typing import Optional

from openai import OpenAI

from apisnap.schema import Route
from apisnap.ai.prompts import get_generate_tests_prompt, get_refine_schema_prompt


CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
DEFAULT_MODEL = "gpt-oss-120b"


class CerebrasClient:
    """Client for Cerebras AI API."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """Initialize Cerebras client.

        Args:
            api_key: Cerebras API key
            model: Model name to use
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=CEREBRAS_BASE_URL,
        )
        self.model = model

    def generate_tests(self, route: Route, framework: str) -> str:
        """Generate tests for a route.

        Args:
            route: Route to generate tests for
            framework: Test framework to use

        Returns:
            Generated test code
        """
        prompt = get_generate_tests_prompt(route, framework)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an API test engineer. Generate complete, runnable test code.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=4000,
            )

            return response.choices[0].message.content
        except Exception as e:
            return f"# Error generating tests: {e}"

    def refine_schema(self, raw_data: dict) -> dict:
        """Refine schema (Pass 1).

        Args:
            raw_data: Raw JSON data

        Returns:
            Refined schema
        """
        prompt = get_refine_schema_prompt(raw_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON schema refinement assistant. Clean up and normalize schemas.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            # Parse response as JSON
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception:
            return raw_data
