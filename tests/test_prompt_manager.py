"""Tests for the prompt manager."""

from pathlib import Path

from src.prompt_manager import PromptManager

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class TestPromptManager:
    def setup_method(self):
        self.manager = PromptManager(PROMPTS_DIR)

    def test_loads_all_prompts(self):
        prompts = self.manager.list_prompts()
        assert len(prompts) >= 50

    def test_get_categories(self):
        categories = self.manager.get_categories()
        expected = {
            "summarization",
            "analysis",
            "code_generation",
            "content_creation",
            "data_extraction",
            "customer_service",
        }
        assert expected.issubset(set(categories))

    def test_get_by_category(self):
        summaries = self.manager.get_by_category("summarization")
        assert len(summaries) >= 8

    def test_get_prompt_by_name(self):
        prompt = self.manager.get_prompt("executive_summary")
        assert prompt is not None
        assert prompt.category == "summarization"

    def test_prompt_has_template(self):
        for prompt in self.manager.list_prompts():
            assert prompt.template.strip(), f"{prompt.name} has empty template"

    def test_prompt_has_metadata(self):
        for prompt in self.manager.list_prompts():
            assert prompt.metadata.recommended_model, f"{prompt.name} missing model"
            assert prompt.metadata.expected_tokens > 0, f"{prompt.name} invalid tokens"

    def test_search_by_name(self):
        results = self.manager.search("summary")
        assert len(results) > 0

    def test_search_by_tag(self):
        results = self.manager.search("business")
        assert len(results) > 0

    def test_render_prompt(self):
        prompt = self.manager.get_prompt("executive_summary")
        if prompt and prompt.examples:
            rendered = prompt.render(**prompt.examples[0].input)
            param_names = [p.name for p in prompt.parameters]
            assert "{document}" not in rendered or "document" not in param_names

    def test_get_stats(self):
        stats = self.manager.get_stats()
        assert stats["total_prompts"] >= 50
        assert stats["categories"] >= 6

    def test_get_nonexistent_prompt(self):
        result = self.manager.get_prompt("nonexistent_prompt_xyz")
        assert result is None

    def test_all_prompts_have_version(self):
        for prompt in self.manager.list_prompts():
            assert prompt.version, f"{prompt.name} missing version"
