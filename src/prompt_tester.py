"""Prompt testing framework with Gemini API integration.

Provides automated testing of prompts against the Gemini API,
measuring quality, latency, and cost metrics.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class TestResult:
    prompt_name: str
    test_input: dict[str, str]
    output: str
    quality_score: float  # 0-10
    latency_ms: float
    token_count: int
    passed: bool
    expected_contains: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_name": self.prompt_name,
            "passed": self.passed,
            "quality_score": self.quality_score,
            "latency_ms": round(self.latency_ms, 1),
            "token_count": self.token_count,
            "missing_keywords": self.missing_keywords,
            "error": self.error,
        }


@dataclass
class BatchTestResult:
    total: int
    passed: int
    failed: int
    results: list[TestResult]
    avg_quality: float
    avg_latency_ms: float

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total > 0 else 0

    def summary(self) -> str:
        lines = [
            f"Test Results: {self.passed}/{self.total} passed ({self.pass_rate:.0f}%)",
            f"Avg Quality: {self.avg_quality:.1f}/10",
            f"Avg Latency: {self.avg_latency_ms:.0f}ms",
        ]
        if self.failed > 0:
            lines.append(f"\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    lines.append(f"  - {r.prompt_name}: {r.error or 'Missing keywords: ' + ', '.join(r.missing_keywords)}")
        return "\n".join(lines)


class PromptTester:
    """Test prompts against the Gemini API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._client = None

    def _get_client(self):
        """Lazy-initialize the Gemini client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(
                    "GEMINI_API_KEY not set. Pass api_key or set GEMINI_API_KEY env var."
                )
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def test_prompt(
        self,
        prompt_path: str | Path,
        test_input: dict[str, str] | None = None,
        model: str | None = None,
    ) -> TestResult:
        """Test a single prompt against the Gemini API."""
        path = Path(prompt_path)
        data = yaml.safe_load(path.read_text())

        prompt_name = data.get("name", path.stem)
        template = data.get("template", "")
        metadata = data.get("metadata", {})
        examples = data.get("examples", [])
        model_name = model or metadata.get("recommended_model", "gemini-2.5-flash-lite")
        temperature = metadata.get("temperature", 0.7)

        # Use provided input or first example
        if test_input:
            input_data = test_input
        elif examples:
            input_data = examples[0].get("input", {})
        else:
            input_data = {}

        expected_contains = []
        if examples and not test_input:
            expected_contains = examples[0].get("expected_output_contains", [])

        # Render template
        rendered = template
        for key, value in input_data.items():
            rendered = rendered.replace(f"{{{key}}}", value)

        # Call the API
        try:
            client = self._get_client()
            start = time.time()

            response = client.models.generate_content(
                model=model_name,
                contents=rendered,
                config={
                    "temperature": temperature,
                    "max_output_tokens": metadata.get("max_tokens", 1024),
                },
            )

            latency_ms = (time.time() - start) * 1000
            output = response.text or ""
            token_count = len(output.split())  # Approximate

            # Check expected content
            missing = [kw for kw in expected_contains if kw.lower() not in output.lower()]
            quality = self._score_quality(output, expected_contains, missing)
            passed = len(missing) == 0 and len(output.strip()) > 0

            return TestResult(
                prompt_name=prompt_name,
                test_input=input_data,
                output=output,
                quality_score=quality,
                latency_ms=latency_ms,
                token_count=token_count,
                passed=passed,
                expected_contains=expected_contains,
                missing_keywords=missing,
            )

        except Exception as e:
            return TestResult(
                prompt_name=prompt_name,
                test_input=input_data,
                output="",
                quality_score=0,
                latency_ms=0,
                token_count=0,
                passed=False,
                error=str(e),
            )

    def test_batch(self, prompts_dir: str | Path, model: str | None = None) -> BatchTestResult:
        """Test all prompts in a directory."""
        results = []
        prompts_path = Path(prompts_dir)

        for yaml_file in sorted(prompts_path.rglob("*.yaml")):
            result = self.test_prompt(yaml_file, model=model)
            results.append(result)

        passed = sum(1 for r in results if r.passed)
        avg_quality = (
            sum(r.quality_score for r in results) / len(results) if results else 0
        )
        avg_latency = (
            sum(r.latency_ms for r in results) / len(results) if results else 0
        )

        return BatchTestResult(
            total=len(results),
            passed=passed,
            failed=len(results) - passed,
            results=results,
            avg_quality=avg_quality,
            avg_latency_ms=avg_latency,
        )

    @staticmethod
    def _score_quality(output: str, expected: list[str], missing: list[str]) -> float:
        """Score output quality on a 0-10 scale."""
        if not output.strip():
            return 0.0

        score = 5.0  # Base score for non-empty output

        # Length bonus
        word_count = len(output.split())
        if word_count >= 50:
            score += 1.0
        if word_count >= 200:
            score += 0.5

        # Expected content bonus
        if expected:
            match_rate = (len(expected) - len(missing)) / len(expected)
            score += match_rate * 3.0

        # Structure bonus
        if any(marker in output for marker in ["- ", "* ", "1.", "## "]):
            score += 0.5

        return min(score, 10.0)

    @staticmethod
    def validate_prompt_format(prompt_path: str | Path) -> list[str]:
        """Validate a prompt YAML file format. Returns list of issues."""
        issues = []
        path = Path(prompt_path)

        try:
            data = yaml.safe_load(path.read_text())
        except Exception as e:
            return [f"Invalid YAML: {e}"]

        if not isinstance(data, dict):
            return ["Root element must be a mapping"]

        required_fields = ["name", "template", "category"]
        for f in required_fields:
            if f not in data:
                issues.append(f"Missing required field: {f}")

        if "template" in data and not data["template"].strip():
            issues.append("Template is empty")

        if "parameters" in data:
            for i, p in enumerate(data["parameters"]):
                if "name" not in p:
                    issues.append(f"Parameter {i} missing 'name'")

        return issues
