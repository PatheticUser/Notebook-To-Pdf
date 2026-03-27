# Notebook-to-PDF (`nb2pdf`)

An intelligent, AI-powered CLI tool that translates Jupyter Notebooks (`.ipynb`) into high-quality, professional PDF reports. 

Instead of mindlessly dumping code cells into a document, `nb2pdf` leverages a LLM to evaluate the necessity of each cell. It skips trivial boilerplate, summarizes complex or messy code blocks, and preserves the essential findings and insights, formatting them elegantly using Markdown and CSS styling.

## Features

- **Intelligent Processing**: Skips noisy imports and `pip install` commands. Summarizes long log outputs.
- **Key Shuffling System**: Bypasses strict API rate limits via a highly scalable API key rotation manager (`llm_manager.py`). 
- **Professional Typography**: Utilizes `weasyprint` with a custom CSS design system optimized for code blocks, margins, fonts, and print layouts.
- **Robust CLI**: Built with `Typer` and visually enhanced using `Rich` for a developer-centric terminal experience.

## Requirements

Ensure you have [uv](https://github.com/astral-sh/uv) installed to manage the Python environment and dependencies seamlessly.

Since this tool produces high-quality layout PDFs via WeasyPrint, ensuring `Pango`, `cairo`, or equivalent OS-level graphics libraries are installed on your Linux system is recommended.

## Installation

Clone the repository and install the dependencies:

```bash
uv add typer rich nbformat groq markdown weasyprint tenacity pydantic
```

## Quick Start

1. Ensure your `api_keys.json` file is present in the local directory. The file must contain a JSON array of valid Groq API strings.
2. Run the application passing in the path to your Jupyter Notebook:

```bash
uv run python3 main.py notebook_name.ipynb
```

### Options

Specify a custom output path for the PDF:
```bash
uv run python3 main.py notebook_name.ipynb -o final_report.pdf
```

Fallback mode (Generate the PDF using pure code logic without API filtering):
```bash
uv run python3 main.py notebook_name.ipynb --no-ai
```

## Architecture

- `parser.py`: Ingests `.ipynb` files into structured Pydantic models.
- `llm_manager.py`: Manages the retry logic and seamless switching of Groq API keys upon encountering rate-limit constraints.
- `analyzer.py`: Crafts prompts around extracted cells and parses JSON decisions via `llama3-8b-8192` models.
- `formatter.py`: Generates the structured intermediate syntax.
- `pdf_gen.py`: Binds custom CSS schemas alongside the final document render logic.
