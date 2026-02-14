# Technical Implementation Plan: AI Skills Builder

## Phase 1: Environment Setup
1. **Initialize Project**: Create directory structure and virtual environment.
2. **Install Dependencies**:
   - `playwright`: For browser automation.
   - `easyocr` or `pytesseract`: For image-to-text processing.
   - `opencv-python`: For image preprocessing.
   - `pillow`: For image handling.

## Phase 2: Browser Automation Core
1. **Chrome Controller**: Develop a script to launch Chrome and navigate to the target URL.
2. **Mode Switcher**: 
   - Capture screenshot.
   - Run OCR to find "Theme" or "Light/Dark" toggle.
   - Click to ensure "Daytime" mode.

## Phase 3: OCR Interaction Engine
1. **Button Discovery**:
   - Scan viewport for "Ask AI" or "Search" strings.
   - Return coordinates of the center of the text.
2. **Chat Interface Discovery**:
   - Identify input area.
   - Detect the sidebar or modal appearance.

## Phase 4: Chat & Skill Extraction
1. **Query Injection**: Simulate typing into the identified input field.
2. **Response Monitoring**: 
   - Wait for "AI is typing" indicators to disappear.
   - OCR the chat response area.
3. **Skill Formatting**:
   - Summarize the response.
   - Save as a markdown skill in the `ASK_AI/skills` directory.

## Phase 5: Demo Construction
1. Target: `https://docs.base.org/get-started/build-app`.
2. Logic: Open -> Toggle Day Mode -> Find Ask AI -> Ask "How do I build a dApp on Base?" -> Scrape response -> Save.
