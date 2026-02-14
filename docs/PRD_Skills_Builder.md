# Product Requirement Document (PRD): AI Skills Builder

## 1. Introduction
The **AI Skills Builder** is a tool designed to enhance the capabilities of AI agents like Claude Code, Gemini CLI, and GitHub Copilot by dynamically fetching context from interactive "Ask AI" widgets on documentation websites. It bridges the gap between static scraping and interactive AI-driven documentation.

## 2. Problem Statement
AI agents often lack the most up-to-date or nuanced context available only through specialized "Ask AI" buttons on developer portals. Standard web scraping often fails to capture the interactive nature of these AI widgets or the dynamic content they provide.

## 3. Goals and Objectives
- **Interactive Context Retrieval**: Automate the process of interacting with site-specific AI assistants.
- **Skill Generation**: Convert retrieved information into "skills" or persistent context files for Claude, Gemini, and Copilot.
- **Visual Validation**: Use OCR to ensure buttons and chat interfaces are correctly identified, regardless of shifting DOM structures.
- **Efficiency**: Minimize token usage by summarizing AI-to-AI interactions.

## 4. Target User
- Developers using AI-assisted coding tools (Claude Code, Gemini CLI).
- Technical writers building automated documentation pipelines.

## 5. Functional Requirements
### 5.1 Browser Automation
- Launch Google Chrome in a controlled environment.
- Navigate to a user-provided URL.
- Handle state changes (e.g., toggling to Daytime mode).

### 5.2 OCR-Driven Interaction
- Capture screenshots of the viewport.
- Identify "Ask AI" buttons using character recognition.
- Identify the "Theme Toggle" (Day/Night) and ensure "Daytime" is active.
- Identify input fields and chat history areas.

### 5.3 AI Interfacing
- Send user-defined queries to the site's AI.
- Listen for and capture the response text via OCR or DOM extraction (with OCR validation).

### 5.4 Skill Output
- Generate a format compatible with AI agents (e.g., `.mcp` definitions, markdown snippets, or system prompt updates).

## 6. Feasibility Analysis
- **Technical Feasibility**: High. Playwright/Puppeteer can handle browser control. Python libraries like `pytesseract` or `EasyOCR` can locate elements.
- **Efficiency**: Moderate. OCR can be slow; optimization (localizing OCR to specific regions) is required.
- **Token Usage**: Critical. Input/Output tokens for the intermediate "Ask AI" must be tracked to prevent cost overruns.

## 7. Performance Requirements
- Site interaction loop < 30 seconds.
- OCR accuracy > 90% for text-based buttons.

## 8. Success Metrics
- Successful retrieval of a relevant technical answer from the target site.
- Automated creation of a "skill" file.
- Correct identification of the "Daytime" mode toggle.
