"""
Documentation Analyzer Module

Uses Playwright for browser automation and Tesseract OCR
to detect developer documentation and ASK AI features on websites.
"""

import asyncio
import io
import os
import re
from typing import Dict, Optional

from app.search_engine import SearchResult

SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")


class DocAnalyzer:
    """Analyzes websites for developer documentation and ASK AI features."""

    # Keywords that indicate a site has developer documentation
    DOC_INDICATORS = [
        "documentation", "docs", "api reference", "api docs",
        "getting started", "quickstart", "tutorial", "developer",
        "guide", "sdk", "reference", "endpoints", "authentication",
        "installation", "setup", "configuration", "examples",
    ]

    # Keywords for finding ASK AI buttons
    ASK_AI_KEYWORDS = ["ask ai", "ask", "ai assistant", "chat with ai"]

    async def check_dev_docs(self, url: str) -> bool:
        """Check if a URL hosts developer documentation."""
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 900}
                )
                page = await context.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

                # Check page content and title for documentation indicators
                content = await page.content()
                title = await page.title()
                content_lower = (content + " " + title).lower()

                score = sum(1 for ind in self.DOC_INDICATORS if ind in content_lower)

                # Also check URL patterns
                url_lower = url.lower()
                if any(p in url_lower for p in ["/docs", "/api", "/reference", "/guide"]):
                    score += 2

                await browser.close()
                return score >= 2

        except Exception as e:
            print(f"[DocAnalyzer] Error checking docs at {url}: {e}")
            return False

    async def find_ask_ai(self, url: str) -> Dict:
        """Find the ASK AI button on a page using OCR."""
        try:
            from playwright.async_api import async_playwright
            import pytesseract
            from PIL import Image

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 900}
                )
                page = await context.new_page()

                await page.goto(url, wait_until="networkidle", timeout=20000)
                await asyncio.sleep(2)

                screenshot = await page.screenshot()
                img = Image.open(io.BytesIO(screenshot))
                ocr_data = pytesseract.image_to_data(
                    img, output_type=pytesseract.Output.DICT
                )

                # Search for "Ask AI" or "Ask" button
                for i, text in enumerate(ocr_data["text"]):
                    text_clean = text.strip().lower()
                    if "ask" in text_clean:
                        # Check if next word is "AI"
                        combined = text_clean
                        if i + 1 < len(ocr_data["text"]):
                            next_word = ocr_data["text"][i + 1].strip().lower()
                            if "ai" in next_word:
                                combined = f"{text_clean} {next_word}"

                        x = ocr_data["left"][i] + (ocr_data["width"][i] // 2)
                        y = ocr_data["top"][i] + (ocr_data["height"][i] // 2)

                        await browser.close()
                        return {
                            "found": True,
                            "x": x,
                            "y": y,
                            "label": combined,
                        }

                # Fallback: check for AI-related buttons via DOM
                ai_selectors = [
                    'button:has-text("Ask AI")',
                    'button:has-text("Ask")',
                    '[data-testid*="ask"]',
                    '[aria-label*="Ask AI"]',
                    '.ask-ai-button',
                ]
                for selector in ai_selectors:
                    try:
                        el = await page.query_selector(selector)
                        if el:
                            box = await el.bounding_box()
                            if box:
                                await browser.close()
                                return {
                                    "found": True,
                                    "x": int(box["x"] + box["width"] / 2),
                                    "y": int(box["y"] + box["height"] / 2),
                                    "label": "Ask AI (DOM)",
                                }
                    except Exception:
                        continue

                await browser.close()
                return {"found": False}

        except Exception as e:
            print(f"[DocAnalyzer] Error finding ASK AI at {url}: {e}")
            return {"found": False, "error": str(e)}

    async def interact_with_ask_ai(self, url: str, query: str) -> Dict:
        """Click the ASK AI button, submit a query, and extract the response."""
        try:
            from playwright.async_api import async_playwright
            import pytesseract
            from PIL import Image

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1280, "height": 900}
                )
                page = await context.new_page()

                await page.goto(url, wait_until="networkidle", timeout=20000)
                await asyncio.sleep(2)

                # Step 1: Find and click ASK AI button
                screenshot = await page.screenshot()
                img = Image.open(io.BytesIO(screenshot))
                ocr_data = pytesseract.image_to_data(
                    img, output_type=pytesseract.Output.DICT
                )

                ask_x, ask_y = -1, -1
                for i, text in enumerate(ocr_data["text"]):
                    if "ask" in text.strip().lower():
                        ask_x = ocr_data["left"][i] + (ocr_data["width"][i] // 2)
                        ask_y = ocr_data["top"][i] + (ocr_data["height"][i] // 2)
                        break

                if ask_x == -1:
                    # Try DOM selectors
                    for selector in [
                        'button:has-text("Ask AI")',
                        'button:has-text("Ask")',
                    ]:
                        try:
                            el = await page.query_selector(selector)
                            if el:
                                box = await el.bounding_box()
                                if box:
                                    ask_x = int(box["x"] + box["width"] / 2)
                                    ask_y = int(box["y"] + box["height"] / 2)
                                    break
                        except Exception:
                            continue

                if ask_x == -1:
                    await browser.close()
                    return {"response": None, "error": "Could not find ASK AI button"}

                # Click the ASK AI button
                await page.mouse.click(ask_x, ask_y)
                await asyncio.sleep(2)

                # Step 2: Find input field and type query
                # Try common input selectors first
                input_typed = False
                input_selectors = [
                    'input[placeholder*="Ask"]',
                    'input[placeholder*="ask"]',
                    'input[placeholder*="question"]',
                    'textarea[placeholder*="Ask"]',
                    'textarea[placeholder*="ask"]',
                    'input[type="text"]',
                    "textarea",
                ]
                for selector in input_selectors:
                    try:
                        el = await page.query_selector(selector)
                        if el and await el.is_visible():
                            await el.click()
                            await el.fill(query)
                            await page.keyboard.press("Enter")
                            input_typed = True
                            break
                    except Exception:
                        continue

                if not input_typed:
                    # Fallback: OCR to find input area
                    screenshot = await page.screenshot()
                    img = Image.open(io.BytesIO(screenshot))
                    ocr_data = pytesseract.image_to_data(
                        img, output_type=pytesseract.Output.DICT
                    )
                    for i, text in enumerate(ocr_data["text"]):
                        if any(w in text.lower() for w in ["ask", "question", "type"]):
                            ix = ocr_data["left"][i]
                            iy = ocr_data["top"][i]
                            await page.mouse.click(ix, iy)
                            await page.keyboard.type(query)
                            await page.keyboard.press("Enter")
                            input_typed = True
                            break

                if not input_typed:
                    await browser.close()
                    return {"response": None, "error": "Could not find input field"}

                # Step 3: Wait for response and extract via OCR
                await asyncio.sleep(8)

                screenshot = await page.screenshot(full_page=False)
                img = Image.open(io.BytesIO(screenshot))
                full_text = pytesseract.image_to_string(img)

                # Clean up OCR text - remove navigation/UI chrome
                cleaned = self._clean_ocr_response(full_text, query)

                await browser.close()
                return {"response": cleaned or full_text}

        except Exception as e:
            print(f"[DocAnalyzer] Error interacting with ASK AI at {url}: {e}")
            return {"response": None, "error": str(e)}

    def _clean_ocr_response(self, raw_text: str, query: str) -> str:
        """Clean OCR output to extract just the AI response portion."""
        lines = raw_text.split("\n")
        cleaned_lines = []
        capture = False

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if capture:
                    cleaned_lines.append("")
                continue

            # Start capturing after we see the query or response indicators
            if any(kw in stripped.lower() for kw in [
                "found results", "here's how", "to get started",
                "you can", "the answer", "based on",
            ]):
                capture = True

            if capture:
                # Skip common UI elements
                if any(skip in stripped.lower() for skip in [
                    "ask a question", "powered by", "©", "cookie",
                    "sign in", "log in", "menu", "navigation",
                ]):
                    continue
                cleaned_lines.append(stripped)

        return "\n".join(cleaned_lines).strip()

    async def save_skill(
        self, site: SearchResult, query: str, response: str
    ) -> str:
        """Save extracted AI response as a reusable skill file."""
        os.makedirs(SKILLS_DIR, exist_ok=True)

        # Generate safe filename
        safe_name = re.sub(r"[^a-z0-9]+", "_", site.title.lower())[:30]
        filename = f"{safe_name}_skill.md"
        filepath = os.path.join(SKILLS_DIR, filename)

        with open(filepath, "w") as f:
            f.write(f"# AI Skill: {site.title}\n\n")
            f.write(f"**Source URL:** {site.url}\n")
            f.write(f"**Query:** {query}\n")
            f.write(f"**Generated by:** ASK AI Skills Builder v0.2.0\n\n")
            f.write(f"## AI Response\n\n")
            f.write(response)
            f.write("\n")

        return filepath
