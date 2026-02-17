# AI Skills Builder (ASK_AI)

An interactive agent that discovers and interfaces with "Ask AI" features on developer documentation sites. It bridges the gap between static documentation and interactive site-specific AI assistants, generating contextual "skills" for Claude Code, Gemini CLI, and GitHub Copilot.

## Overview

The AI Skills Builder provides a **web-based conversational interface** where users describe what technology they're looking for. The agent then:

1. Searches the web for relevant documentation sites (Google ADK-style deep search)
2. Lets the user select a site from the results
3. Checks the site for developer documentation
4. Looks for an "ASK AI" button using OCR visual recognition
5. Interacts with the site's AI assistant and extracts the response
6. Generates a reusable skill file

## Features

- **Web Interface**: Chat-based UI with real-time agent status on port 8074
- **Voice Input**: Speech-to-text via Web Speech API
- **Agent Status Panel**: Shows state machine transitions for developer visibility
- **Visual Button Discovery**: Uses Tesseract OCR to find "Ask AI" buttons
- **Smart Fallbacks**: DOM selectors as fallback when OCR is insufficient
- **Search Integration**: Web search with curated fallback for reliability
- **Retry Logic**: Up to 3 site attempts per session
- **Skill Generation**: Saves extracted AI responses as reusable Markdown files

## Setup

### Prerequisites
- **Python 3.11+**
- **Tesseract OCR Engine**:
  - Linux: `sudo apt install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

### Installation
1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Linux/macOS
   # .venv\Scripts\activate   # On Windows
   ```

2. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

## Usage

### Web Interface (Recommended)
From the `ASK_AI` directory:
```bash
# Ensure the app is in your python path if running modules directly
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -m app.main
```
Or use **uvicorn** directly:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8074
```
Then open [http://localhost:8074](http://localhost:8074) in your browser.

### Demo Script
```bash
# Automated demo (starts server + walks through conversation)
python demo_script.py

# Interactive mode (just starts the server)
python demo_script.py --interactive
```

### Original CLI Demo
```bash
python demo_poc.py
```

## Testing
```bash
# Run all tests with rubric report
python -m pytest tests/ -v -s

# The rubric report shows weighted scores against PRD requirements
```

## Project Structure
```
app/
  main.py              # FastAPI server (port 8074)
  agent.py             # State-machine conversation agent
  search_engine.py     # Google ADK-style deep search
  doc_analyzer.py      # Playwright + OCR browser automation
  static/              # Web interface (HTML/CSS/JS)
tests/
  conftest.py          # RubricTracker + fixtures
  test_unit.py         # Unit tests (17 tests)
  test_integration.py  # Integration tests (11 tests)
docs/
  PRD_Skills_Builder.md
  Implementation_Plan.md
  Testing_Rubrics.md
  fixes/               # Fix documentation and prompts
```

## Documentation
- [Product Requirement Document](docs/PRD_Skills_Builder.md)
- [Implementation Plan v2](docs/fixes/implementation_plan_v2.md)
- [Testing Rubrics](docs/Testing_Rubrics.md)
- [Fix Request Prompt](docs/fixes/prompt.md)

## License
This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.
