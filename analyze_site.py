import asyncio
from playwright.async_api import async_playwright
import pytesseract
from PIL import Image
import io
import os

async def analyze_site():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        url = "https://docs.base.org/get-started/build-app"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")
        
        # Take a full screenshot for OCR analysis
        screenshot_bytes = await page.screenshot(full_page=False)
        img = Image.open(io.BytesIO(screenshot_bytes))
        
        # Perform OCR to find specific elements
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        print("\n--- OCR Analysis Results ---")
        targets = ["ASK", "AI", "Day", "Night", "Theme", "Light", "Dark"]
        for i, text in enumerate(ocr_data['text']):
            if any(t.lower() in text.lower() for t in targets) and text.strip():
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                print(f"Found '{text}' at ({x}, {y}) with size {w}x{h}")

        # Check for the daytime toggle (specifically looking for dark/light mode indicator)
        # Often these are icons, so we might need to look for buttons nearby text
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_site())
