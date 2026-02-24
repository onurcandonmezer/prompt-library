"""Prompt management engine — CRUD, search, and versioning for prompt templates.

Provides structured access to the prompt library with category-based
organization, search capabilities, and metadata management.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PromptParameter:
    name: str
    type: str = "string"
    required: bool = True
    description: str = ""
    default: str | None = None


@dataclass
class PromptExample:
    input: dict[str, str]
    expected_output_contains: list[str] = field(default_factory=list)
    expected_output: str | None = None


@dataclass
class PromptMetadata:
    recommended_model: str = "gemini-2.5-flash-lite"
    expected_tokens: int = 500
    temperature: float = 0.7
    tags: list[str] = field(default_factory=list)
    max_tokens: int | None = None


@dataclass
class Prompt:
    name: str
    version: str
    category: str
    description: str
    template: str
    parameters: list[PromptParameter] = field(default_factory=list)
    metadata: PromptMetadata = field(default_factory=PromptMetadata)
    examples: list[PromptExample] = field(default_factory=list)
    file_path: str | None = None

    def render(self, **kwargs: str) -> str:
        """Render the prompt template with provided parameters."""
        text = self.template
        for param in self.parameters:
            key = param.name
            if key in kwargs:
                text = text.replace(f"{{{key}}}", str(kwargs[key]))
            elif param.required and param.default is None:
                raise ValueError(f"Missing required parameter: {key}")
            elif param.default is not None:
                text = text.replace(f"{{{key}}}", param.default)
        return text

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "category": self.category,
            "description": self.description,
            "template": self.template,
            "parameters": [
                {"name": p.name, "type": p.type, "required": p.required}
                for p in self.parameters
            ],
            "metadata": {
                "recommended_model": self.metadata.recommended_model,
                "expected_tokens": self.metadata.expected_tokens,
                "temperature": self.metadata.temperature,
                "tags": self.metadata.tags,
            },
        }


class PromptManager:
    """Manage a library of prompt templates."""

    def __init__(self, prompts_dir: str | Path = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._cache: dict[str, Prompt] = {}
        self._load_all()

    def _load_all(self):
        """Load all prompts from the prompts directory."""
        if not self.prompts_dir.exists():
            return
        for yaml_file in self.prompts_dir.rglob("*.yaml"):
            try:
                prompt = self._load_prompt(yaml_file)
                self._cache[prompt.name] = prompt
            except Exception:
                continue

    def _load_prompt(self, path: Path) -> Prompt:
        """Load a single prompt from a YAML file."""
        data = yaml.safe_load(path.read_text())

        parameters = [
            PromptParameter(
                name=p["name"],
                type=p.get("type", "string"),
                required=p.get("required", True),
                description=p.get("description", ""),
                default=p.get("default"),
            )
            for p in data.get("parameters", [])
        ]

        meta_data = data.get("metadata", {})
        metadata = PromptMetadata(
            recommended_model=meta_data.get("recommended_model", "gemini-2.5-flash-lite"),
            expected_tokens=meta_data.get("expected_tokens", 500),
            temperature=meta_data.get("temperature", 0.7),
            tags=meta_data.get("tags", []),
            max_tokens=meta_data.get("max_tokens"),
        )

        examples = [
            PromptExample(
                input=ex.get("input", {}),
                expected_output_contains=ex.get("expected_output_contains", []),
                expected_output=ex.get("expected_output"),
            )
            for ex in data.get("examples", [])
        ]

        return Prompt(
            name=data["name"],
            version=data.get("version", "1.0"),
            category=data.get("category", "uncategorized"),
            description=data.get("description", ""),
            template=data.get("template", ""),
            parameters=parameters,
            metadata=metadata,
            examples=examples,
            file_path=str(path),
        )

    def list_prompts(self) -> list[Prompt]:
        """List all prompts in the library."""
        return sorted(self._cache.values(), key=lambda p: (p.category, p.name))

    def get_prompt(self, name: str) -> Prompt | None:
        """Get a prompt by name."""
        return self._cache.get(name)

    def get_by_category(self, category: str) -> list[Prompt]:
        """Get all prompts in a category."""
        return [p for p in self._cache.values() if p.category == category]

    def get_categories(self) -> list[str]:
        """Get all available categories."""
        return sorted(set(p.category for p in self._cache.values()))

    def search(self, query: str) -> list[Prompt]:
        """Search prompts by name, description, or tags."""
        query_lower = query.lower()
        results = []
        for prompt in self._cache.values():
            if (
                query_lower in prompt.name.lower()
                or query_lower in prompt.description.lower()
                or any(query_lower in tag.lower() for tag in prompt.metadata.tags)
            ):
                results.append(prompt)
        return results

    def get_stats(self) -> dict[str, Any]:
        """Get library statistics."""
        prompts = self.list_prompts()
        categories = self.get_categories()
        return {
            "total_prompts": len(prompts),
            "categories": len(categories),
            "category_counts": {
                cat: len(self.get_by_category(cat)) for cat in categories
            },
            "models_used": list(set(p.metadata.recommended_model for p in prompts)),
        }


def main():
    parser = argparse.ArgumentParser(description="Prompt Library Manager")
    sub = parser.add_subparsers(dest="command")

    list_parser = sub.add_parser("list", help="List all prompts")
    list_parser.add_argument("--category", default=None)
    list_parser.add_argument("--dir", default="prompts")

    search_parser = sub.add_parser("search", help="Search prompts")
    search_parser.add_argument("query")
    search_parser.add_argument("--dir", default="prompts")

    stats_parser = sub.add_parser("stats", help="Show library statistics")
    stats_parser.add_argument("--dir", default="prompts")

    args = parser.parse_args()

    if args.command == "list":
        manager = PromptManager(args.dir)
        prompts = (
            manager.get_by_category(args.category) if args.category else manager.list_prompts()
        )
        for p in prompts:
            print(f"  [{p.category}] {p.name} v{p.version} — {p.description}")

    elif args.command == "search":
        manager = PromptManager(args.dir)
        results = manager.search(args.query)
        for p in results:
            print(f"  [{p.category}] {p.name} — {p.description}")

    elif args.command == "stats":
        manager = PromptManager(args.dir)
        stats = manager.get_stats()
        print(f"Total prompts: {stats['total_prompts']}")
        print(f"Categories: {stats['categories']}")
        for cat, count in stats["category_counts"].items():
            print(f"  {cat}: {count}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
