"""Tests for the prompt tester (offline validation only)."""

from pathlib import Path

from src.prompt_tester import PromptTester


PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class TestPromptTesterValidation:
    """Test prompt format validation without API calls."""

    def test_validate_all_prompt_formats(self):
        """Every prompt YAML should pass format validation."""
        for yaml_file in PROMPTS_DIR.rglob("*.yaml"):
            issues = PromptTester.validate_prompt_format(yaml_file)
            assert issues == [], f"{yaml_file.name} has issues: {issues}"

    def test_all_prompts_have_required_fields(self):
        """All prompts must have name, template, and category."""
        import yaml

        for yaml_file in PROMPTS_DIR.rglob("*.yaml"):
            data = yaml.safe_load(yaml_file.read_text())
            assert "name" in data, f"{yaml_file.name} missing 'name'"
            assert "template" in data, f"{yaml_file.name} missing 'template'"
            assert "category" in data, f"{yaml_file.name} missing 'category'"

    def test_all_prompts_have_examples(self):
        """All prompts should include at least one example."""
        import yaml

        for yaml_file in PROMPTS_DIR.rglob("*.yaml"):
            data = yaml.safe_load(yaml_file.read_text())
            examples = data.get("examples", [])
            assert len(examples) > 0, f"{yaml_file.name} has no examples"

    def test_quality_scorer(self):
        """Test the static quality scoring method."""
        score = PromptTester._score_quality(
            output="This is a test output with bullet points:\n- Item 1\n- Item 2",
            expected=["test", "bullet"],
            missing=[],
        )
        assert score > 5.0

    def test_quality_scorer_empty_output(self):
        score = PromptTester._score_quality("", [], [])
        assert score == 0.0

    def test_quality_scorer_missing_keywords(self):
        score_full = PromptTester._score_quality("test output", ["test"], [])
        score_missing = PromptTester._score_quality("test output", ["test", "missing"], ["missing"])
        assert score_full > score_missing
