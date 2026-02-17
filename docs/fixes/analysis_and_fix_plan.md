# Codebase Analysis and Fix Recommendations: ASK AI Skills Builder

**Date:** 2026-02-17  
**Location:** [/llm_models_python_code_src/ASK_AI/docs/fixes/analysis_and_fix_plan.md](/llm_models_python_code_src/ASK_AI/docs/fixes/analysis_and_fix_plan.md)

---

## 1. Analysis of Current Implementation vs. Original Prompt

### What Got Right:
- **Web Interface**: A FastAPI/WebSocket chat interface is implemented on port **8074** as requested.
- **Agent Status Observability**: The `ConversationAgent` emits granular status updates (e.g., `searching`, `checking_docs`) which are displayed in the UI.
- **OCR Interaction**: The `DocAnalyzer` correctly implements `pytesseract` to find buttons and extract text from documentation sites.
- **Workflow Skeleton**: The state machine in `agent.py` follows the requested flow (Gathering -> Searching -> Selection -> Checking).
- **Retry Logic**: Implements the 3-site iteration limit when documentation is not found.

### What Got Wrong / Broken Parts:
- **Deep Search Integration**: `search_engine.py` is a placeholder using `duckduckgo-search`. It mentions Google ADK but doesn't actually implement it. The user specifically requested a "deep search" similar to the `adk-python-examples/python/agents/deep-search` codebase.
- **False Negative in Doc Detection**: The user reported that the agent says "no public developer documentation found" even when valid URLs are provided. 
    - **Cause**: The `DOC_INDICATORS` score threshold in `doc_analyzer.py` is too restrictive or failing on specific modern layouts (like Base docs) where content is heavily async or uses custom headers.
    - **Cause**: The `check_dev_docs` method uses `domcontentloaded` wait, which might miss dynamically rendered documentation labels.
- **"Next Status" Progression**: The agent gets stuck in the `CHECKING_DOCS` -> `NO_DOCS` loop because the heuristic analyzer fails to "see" the documentation on the page.

---

## 2. Comparison with `deep-search` Reference
The reference codebase in `adk-python-examples` uses a sophisticated `LoopAgent` with grounding metadata and structured `Feedback` (pass/fail). 
- **ASK_AI** current search is static.
- **Suggestion**: Enhance `SearchEngine` to use a more robust search pattern if available, or at least improve the "deep" aspect by crawling 1-level deep into the selected site to verify docs.

---

## 3. Technical Fix Plan: Broken Parts Only

### Fix 1: Documentation Detection Heuristics
The current `score >= 2` logic is too primitive. I will update `doc_analyzer.py` to:
1. Increase timeout and use `networkidle` to ensure JS-heavy docs load.
2. Scan for metadata tags (OpenGraph, meta description) which often contain "documentation" keywords.
3. Loosen the keyword check to be more context-aware of site headers.

### Fix 2: Search Engine Reliability
Update `search_engine.py` to better handle the "Deep Search" requirement by ensuring it prioritizes "developers" and "docs" subdomains in its ranking, mimicking the ADK agent's focus.

### Fix 3: Agent State Loop
Fix the `_handle_no_docs_response` and `_check_developer_docs` transition to ensure that if a user points to a site that *is* a doc site, the agent doesn't fail.

---

## 4. Testing Rubric for Fixes

| Test Type | Target | Metric for Success |
|-----------|--------|--------------------|
| **Unit** | `DocAnalyzer.check_dev_docs` | Must return `True` for `https://docs.base.org/get-started/build-app` |
| **Unit** | `DocAnalyzer.find_ask_ai` | Must return coordinates for the "Ask AI" button on Base docs |
| **Integration** | Full Site Selection Loop | Selecting "1" from results must transition to `FOUND_DOCS` within 10s |
| **Regression** | Retry Limit | Max 3 attempts must be strictly enforced before `ENDED` state |

---

## 5. Implementation Suggestions

```python
# In app/doc_analyzer.py
# 1. Change wait_until to "networkidle" to catch dynamic docs
# 2. Add technical meta-tag scanning
# 3. Add common doc platform selectors (GitBook, Docusaurus, Mintlify)
```

**Proceeding with fixes to `app/doc_analyzer.py` and `app/search_engine.py` to resolve the reported "no documentation found" issue.**
