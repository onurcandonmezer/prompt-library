<h1 align="center">📝 Prompt Library</h1>

<p align="center">
  <strong>Enterprise prompt engineering library with testing, versioning, and management</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Prompts-50+-4285F4?style=flat-square" alt="Prompts"/>
  <img src="https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Google_Gemini-API-8E75B2?style=flat-square&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/github/actions/workflow/status/onurcandonmezer/prompt-library/ci.yml?style=flat-square&label=CI" alt="CI"/>
</p>

---

## Overview

A structured, enterprise-grade prompt engineering library. Prompts are treated as **managed assets** — categorized, versioned, tested, and documented with metadata including model recommendations, expected token usage, and example inputs/outputs.

Includes a **Streamlit management UI** for browsing, testing, and managing prompts, plus a **testing framework** for automated quality validation against the Gemini API.

## Key Features

- **50+ Categorized Prompts** — Organized across 6 domains: summarization, analysis, code generation, content creation, data extraction, and customer service
- **YAML-Based Format** — Each prompt includes metadata, parameters, model recommendation, and example I/O
- **Prompt Testing Framework** — Automated testing with Gemini API for quality validation and regression detection
- **Streamlit Management UI** — Browse, search, test, and manage prompts through an interactive dashboard
- **Version Tracking** — Track prompt versions with changelog and performance metrics
- **Quality Metrics** — Track response quality, latency, and cost per prompt

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI (app.py)                     │
├─────────────────────────────────────────────────────────────┤
│            Prompt Manager — CRUD & Search Engine              │
├──────────────────────┬──────────────────────────────────────┤
│   Prompt Tester      │       Prompt Templates (YAML)         │
│   (Gemini API)       │   6 categories × ~9 prompts each     │
└──────────────────────┴──────────────────────────────────────┘
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/onurcandonmezer/prompt-library.git
cd prompt-library
make install

# Browse prompts
python -m src.prompt_manager list

# Test a prompt with Gemini API (bring your own key)
cp .env.example .env  # then add your GEMINI_API_KEY
export GEMINI_API_KEY="your-api-key-here"
python -m src.prompt_tester --prompt prompts/summarization/executive_summary.yaml

# Launch the Streamlit UI
make run
```

## Usage Examples

### Browse Prompts Programmatically

```python
from src.prompt_manager import PromptManager

manager = PromptManager(prompts_dir="prompts")
all_prompts = manager.list_prompts()
summaries = manager.get_by_category("summarization")

prompt = manager.get_prompt("executive_summary")
print(f"Name: {prompt.name}")
print(f"Template: {prompt.template}")
print(f"Recommended Model: {prompt.metadata.recommended_model}")
```

### Test a Prompt

```python
from src.prompt_tester import PromptTester

tester = PromptTester(api_key=os.environ["GEMINI_API_KEY"])
result = tester.test_prompt(
    prompt_path="prompts/summarization/executive_summary.yaml",
    test_input="Your test document text here...",
)
print(f"Quality Score: {result.quality_score}/10")
print(f"Latency: {result.latency_ms}ms")
print(f"Output: {result.output}")
```

## Prompt Format

Each prompt is a YAML file with this structure:

```yaml
name: executive_summary
version: "1.0"
category: summarization
description: "Generate an executive summary from a document"

template: |
  Summarize the following document into a concise executive summary.
  Focus on key findings, decisions, and action items.

  Document:
  {document}

parameters:
  - name: document
    type: string
    required: true
    description: "The document text to summarize"

metadata:
  recommended_model: "gemini-2.5-flash-lite"
  expected_tokens: 500
  temperature: 0.3
  tags: ["business", "document", "summary"]

examples:
  - input:
      document: "Q3 revenue grew 15%..."
    expected_output_contains: ["revenue", "growth"]
```

## Tech Stack

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Google_Gemini-8E75B2?style=flat-square&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/YAML-CB171E?style=flat-square&logo=yaml&logoColor=white" alt="YAML"/>
  <img src="https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white" alt="Pydantic"/>
</p>

## Project Structure

```
prompt-library/
├── README.md
├── pyproject.toml
├── Makefile
├── prompts/
│   ├── summarization/        # 9 summarization prompts
│   ├── analysis/             # 9 analysis prompts
│   ├── code_generation/      # 8 code generation prompts
│   ├── content_creation/     # 8 content creation prompts
│   ├── data_extraction/      # 8 data extraction prompts
│   └── customer_service/     # 8 customer service prompts
├── src/
│   ├── prompt_manager.py     # CRUD & search engine
│   ├── prompt_tester.py      # Gemini API testing
│   └── app.py                # Streamlit UI
├── tests/
│   ├── test_prompt_manager.py
│   └── test_prompt_tester.py
└── .github/
    └── workflows/
        └── ci.yml
```

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  Built for enterprise prompt engineering by <a href="https://github.com/onurcandonmezer">Onurcan Dönmezer</a>
</p>
