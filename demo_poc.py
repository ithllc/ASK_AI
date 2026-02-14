import asyncio
from playwright.async_api import async_playwright
import pytesseract
from PIL import Image
import io
import time
import os

# Configuration
URL = "https://docs.base.org/get-started/build-app"
ASK_AI_QUERY = "How do I build a dApp on Base using OnchainKit?"
SKILLS_DIR = "/llm_models_python_code_src/ASK_AI/skills"

async def run_demo():
    if not os.path.exists(SKILLS_DIR):
        os.makedirs(SKILLS_DIR)

    async with async_playwright() as p:
        print("🚀 Launching Chrome...")
        browser = await p.chromium.launch(headless=True) # Set to False if you want to see it
        context = await browser.new_context(viewport={'width': 1280, 'height': 900})
        page = await context.new_page()
        
        print(f"🌐 Navigating to {URL}...")
        await page.goto(URL, wait_until="networkidle")
        await asyncio.sleep(2) # Give it a moment to settle

        # Step 1: Ensure Daytime Mode
        # The user requested daytime mode. We'll look for the toggle.
        # Often it's a button with 'light' or 'dark' or a sun/moon icon.
        # Based on previous OCR, we didn't see 'light' or 'dark' immediately.
        # Let's try to click the body and look for theme classes if OCR fails, 
        # but the prompt specifically says "Use OCR to confirm".
        
        print("📸 Capturing screenshot for Theme Toggle discovery...")
        screenshot = await page.screenshot()
        img = Image.open(io.BytesIO(screenshot))
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        # Look for theme related words or just check current state
        # For this demo, we'll assume we can find it via common selectors if OCR is elusive, 
        # but per instructions, we must use OCR to confirm the daytime/nighttime toggle button.
        
        found_toggle = False
        for i, text in enumerate(ocr_data['text']):
            if any(word in text.lower() for word in ["theme", "light", "dark", "mode"]):
                x, y = ocr_data['left'][i], ocr_data['top'][i]
                print(f"🎯 Found Theme Toggle candidate: '{text}' at ({x}, {y})")
                await page.mouse.click(x + 5, y + 5)
                found_toggle = True
                break
        
        if not found_toggle:
            print("⚠️ OCR couldn't find 'Theme' text. Attempting to find by icon positioning (top right)...")
            # Usually theme toggles are top right.
            await page.mouse.click(1200, 30) 

        # Step 2: Find "ASK AI" Button
        print("📸 Searching for 'ASK AI' button via OCR...")
        screenshot = await page.screenshot()
        img = Image.open(io.BytesIO(screenshot))
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        ask_x, ask_y = -1, -1
        for i, text in enumerate(ocr_data['text']):
            if "ask" in text.lower(): # Looking for "Ask" or "ASK AI"
                # Check if next word is "AI"
                current_text = text
                if i + 1 < len(ocr_data['text']):
                    next_text = ocr_data['text'][i+1]
                    if "ai" in next_text.lower():
                        current_text += " " + next_text
                
                ask_x = ocr_data['left'][i] + (ocr_data['width'][i] // 2)
                ask_y = ocr_data['top'][i] + (ocr_data['height'][i] // 2)
                print(f"✅ Found '{current_text}' button at ({ask_x}, {ask_y})")
                break
        
        if ask_x != -1:
            print(f"🖱️ Clicking 'ASK AI' button...")
            await page.mouse.click(ask_x, ask_y)
            await asyncio.sleep(2) # Wait for sidebar/modal
        else:
            print("❌ Could not find 'ASK AI' button via OCR.")
            await browser.close()
            return

        # Step 3: Interface with the AI
        print("⌨️ Sending query to AI interface...")
        # Now we need to find the input field. OCR can help find "Ask a question" placeholder.
        screenshot = await page.screenshot()
        img = Image.open(io.BytesIO(screenshot))
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        
        input_x, input_y = -1, -1
        for i, text in enumerate(ocr_data['text']):
            if any(word in text.lower() for word in ["ask", "question", "type", "message"]):
                input_x = ocr_data['left'][i]
                input_y = ocr_data['top'][i]
                print(f"📍 Found likely input area via text '{text}' at ({input_x}, {input_y})")
                break
        
        if input_x != -1:
            await page.mouse.click(input_x, input_y)
            await page.keyboard.type(ASK_AI_QUERY)
            await page.keyboard.press("Enter")
            print("⏳ Waiting for AI response...")
            await asyncio.sleep(10) # Wait for response to generate
        else:
            # Fallback for input field if OCR text is missing inside the box
            print("⚠️ OCR didn't find input text. Trying to find input element...")
            await page.keyboard.press("Tab") # Sometimes tab helps
            await page.keyboard.type(ASK_AI_QUERY)
            await page.keyboard.press("Enter")
            await asyncio.sleep(10)

        # Step 4: Extract Response using OCR
        print("📖 Reading AI response via OCR...")
        screenshot = await page.screenshot()
        img = Image.open(io.BytesIO(screenshot))
        full_text = pytesseract.image_to_string(img)
        
        # Filter response - usually it's in a specific area, but for POC we'll take the whole thing
        # In a real tool, we'd OCR just the sidebar region.
        
        skill_filename = f"{SKILLS_DIR}/base_dapp_skill.md"
        with open(skill_filename, "w") as f:
            f.write(f"# AI Skill: Building dApps on Base\n\n")
            f.write(f"**Source URL:** {URL}\n")
            f.write(f"**Query:** {ASK_AI_QUERY}\n\n")
            f.write(f"## AI Response (Scraped via OCR)\n\n")
            f.write(full_text)
        
        print(f"⭐ Skill generated successfully: {skill_filename}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_demo())
