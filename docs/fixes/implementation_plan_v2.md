# Technical Implementation Plan v2 - ASK AI Skills Builder

**Date:** 2026-02-14
**Status:** Implemented
**Fixes Applied To:** Original demo_poc.py and analyze_site.py

---

## Issues Found in Original Code

### Critical Issues
1. **No web interface** - Only CLI scripts, no way for users to interact
2. **Hardcoded to single site** - Only works with docs.base.org
3. **No search capability** - Cannot discover documentation sites
4. **No conversational flow** - No state machine, no user interaction
5. **No tests** - Zero test coverage
6. **No error recovery** - Crashes on failure without retry logic
7. **Fragile OCR** - Full-page OCR captures UI chrome mixed with content

### Moderate Issues
8. **No modular architecture** - Monolithic scripts
9. **Long sleep waits** - 10-second sleeps instead of smart waiting
10. **No status feedback** - User has no visibility into what's happening
11. **License mismatch** - pyproject.toml says MIT, LICENSE file is AGPL v3

---

## Architecture (v2)

```
app/
├── __init__.py          # Package init
├── main.py              # FastAPI server (port 8074)
├── agent.py             # State-machine conversation agent
├── search_engine.py     # Google ADK-style deep search
├── doc_analyzer.py      # Playwright + OCR browser automation
└── static/
    ├── index.html       # Web interface
    ├── style.css        # Dark developer theme
    └── app.js           # Frontend (WebSocket, voice, status)

tests/
├── __init__.py
├── conftest.py          # Rubric tracker + fixtures
├── test_unit.py         # Unit tests with rubric scoring
└── test_integration.py  # Integration tests with rubric scoring
```

---

## Implementation Phases

### Phase 1: Core Architecture (Fixes #1, #2, #8)
- Created modular package structure under `app/`
- Separated concerns: search, analysis, agent logic, web serving
- Made all components configurable and reusable

### Phase 2: Search Integration (Fixes #2, #3)
- Implemented `SearchEngine` class following Google ADK patterns
- Primary: DuckDuckGo search (no API key needed for POC)
- Fallback: Curated results for demo reliability
- Returns structured `SearchResult` objects

### Phase 3: Conversational Agent (Fixes #4, #6)
- Built `ConversationAgent` with 13-state state machine:
  ```
  INTRO → GATHERING → SEARCHING → PRESENTING_RESULTS →
  AWAITING_SELECTION → CHECKING_DOCS → [FOUND_DOCS | NO_DOCS] →
  CHECKING_ASK_AI → INTERACTING_AI → EXTRACTING → COMPLETE → ENDED
  ```
- Max 3 site retries per PRD
- Graceful error handling at every state
- Status callbacks for real-time UI updates

### Phase 4: Web Interface (Fixes #1, #10)
- FastAPI with WebSocket for real-time communication
- Dark theme, developer-focused design
- Left sidebar: Agent status panel with state machine visualization
- Activity log showing timestamped events
- Voice input via Web Speech API
- Markdown rendering in chat messages
- Runs on port 8074

### Phase 5: Browser Automation (Fixes #7, #9)
- Enhanced `DocAnalyzer` with:
  - Keyword-based documentation detection (17 indicators)
  - OCR + DOM fallback for ASK AI button detection
  - Smart input field discovery (DOM selectors before OCR)
  - Response cleaning to strip UI chrome
  - Configurable timeouts

### Phase 6: Testing & Rubric System (Fix #5)
- `RubricTracker` class for scoring tests against PRD criteria
- 20+ unit tests across 5 categories
- 10+ integration tests for conversation flow
- Rubric report generated at end of test session
- Scoring: weighted pass/fail with 70% threshold

---

## Test Rubric System

### Unit Test Categories
| Category | Tests | Weight |
|----------|-------|--------|
| Search Engine | Result structure, fallback, relevance, URL format | 5.0 |
| Agent State Machine | Initial state, transitions, components, states | 9.0 |
| Doc Analyzer | Indicators, keywords, OCR cleaning, file gen | 6.0 |
| Configuration | Paths, enum values | 1.0 |

### Integration Test Categories
| Category | Tests | Weight |
|----------|-------|--------|
| Conversation Flow | Intro→Search, invalid selection | 5.0 |
| Retry Logic | No-docs retry, max retries | 4.0 |
| Search Integration | Structured results | 2.0 |
| FastAPI | App init, health, static files | 4.0 |
| WebSocket | Message format, status format | 2.0 |

### Pass Criteria
- Individual test: Binary pass/fail
- Overall: >= 70% weighted score
- Report generated via `pytest -s` (prints rubric at end)

---

## Dependencies Added
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `websockets` - WebSocket support
- `duckduckgo-search` - Web search (Google ADK fallback)
- `pytest` + `pytest-asyncio` - Testing framework
- `httpx` - HTTP client for testing

---

## Addendums to Original Documentation

### PRD Addendum
- **Web Interface Requirement**: Users must be able to interact via browser
- **Voice Input**: Web Speech API for speech-to-text
- **Status Visibility**: Real-time agent state shown to all skill levels
- **Search Integration**: Google ADK-style deep search for site discovery
- **Retry Logic**: Max 3 site attempts per session

### Testing Rubric Addendum
- All tests scored and weighted against PRD requirements
- Rubric report auto-generated on test completion
- 70% minimum threshold for overall pass
