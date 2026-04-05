import sys
import os
import time
import re
from pathlib import Path

# Use local dependencies copied to the project root
from auth_manager import AuthManager
from browser_utils import BrowserFactory, StealthUtils
from config import QUERY_INPUT_SELECTORS, RESPONSE_SELECTORS
from patchright.sync_api import sync_playwright

# Extend selectors for Korean
KOREAN_QUERY_SELECTORS = [
    'textarea[placeholder="질문 입력"]',
    'textarea[aria-label="질문 입력"]',
    'textarea[placeholder="Enter a query"]',
]
ALL_QUERY_SELECTORS = KOREAN_QUERY_SELECTORS + QUERY_INPUT_SELECTORS

class NotebookReporter:
    def __init__(self, notebook_url):
        self.notebook_url = notebook_url
        self.auth = AuthManager()

    def generate_report(self, prompt):
        """
        Asks NotebookLM to generate a report based on the prompt.
        """
        if not self.auth.is_authenticated():
            print("[Reporter] Not authenticated. Cannot generate report.")
            return None

        print(f"[Reporter] Generating report using prompt: {prompt[:30]}...")
        
        with sync_playwright() as p:
            # Use BrowserFactory to ensure correct browser path and arguments
            context = BrowserFactory.launch_persistent_context(p, headless=False)
            
            page = context.new_page()
            try:
                page.goto(self.notebook_url, wait_until="domcontentloaded")
                
                # Wait for NotebookLM to load
                page.wait_for_url(re.compile(r"^https://notebooklm\.google\.com/"), timeout=60000)
                
                # Try to close any open dialogs
                try:
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                except:
                    pass

                # Wait for query input
                print("[Reporter] Waiting for query input...")
                query_element = None
                
                # Try to find the query input, handling localizations
                for selector in ALL_QUERY_SELECTORS:
                    try:
                        # check distinct selectors
                        elements = page.locator(selector)
                        count = elements.count()
                        for i in range(count):
                            el = elements.nth(i)
                            if el.is_visible():
                                # Check placeholder to ensure it's not the source search
                                placeholder = el.get_attribute("placeholder")
                                if placeholder and "웹에서 새 소스" in placeholder:
                                    continue
                                
                                query_element = el
                                print(f"[Reporter] Found input: {selector}")
                                break
                        if query_element:
                            break
                    except:
                        continue
                
                if not query_element:
                    # Fallback: Just look for any textarea at the bottom
                    query_element = page.locator("textarea").last
                    if not query_element.is_visible():
                         print("[Reporter] Could not find query input")
                         return None
                
                # Type prompt with retry
                print("[Reporter] typing prompt...")
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Re-locate element to avoid detachment
                        query_element = None
                        for selector in ALL_QUERY_SELECTORS:
                            if page.locator(selector).count() > 0 and page.locator(selector).first.is_visible():
                                query_element = page.locator(selector).first
                                break
                        
                        if not query_element:
                            query_element = page.locator("textarea").last
                        
                        if query_element and query_element.is_visible():
                            query_element.fill(prompt)
                            time.sleep(1)
                            page.keyboard.press("Enter")
                            break
                        else:
                            raise Exception("Input element not found during retry")
                    except Exception as e:
                        print(f"[Reporter] Warning: Failed to type prompt (Attempt {attempt+1}/{max_retries}): {e}")
                        time.sleep(2)
                        
                        if attempt == max_retries - 1:
                            raise e
                
                # Wait for response
                print("[Reporter] Waiting for response...")
                # Simplified wait logic: Wait for "Thinking" then wait for static text
                
                # Wait for thinking to appear (optional, might be too fast)
                time.sleep(2)
                
                # Wait for answer to stabilize
                answer = self._wait_for_answer(page)
                return answer

            except Exception as e:
                print(f"[Reporter] Error generating report: {e}")
                import traceback
                traceback.print_exc()
                return None
            finally:
                context.close()

    def generate_slide_content(self, prompt):
        """
        Asks NotebookLM to generate slide content (Title + Bullets).
        Returns a list of dicts: [{'title': '...', 'content': ['...', '...']}]
        """
        raw_text = self.generate_report(prompt)
        if not raw_text:
            return []
        
        # Simple parser for the expected format
        # Format expectation:
        # Title: [Title Text]
        # - [Bullet Point]
        # - [Bullet Point]
        #
        # Title: [Next Title]
        # ...
        
        slides = []
        current_slide = None
        
        lines = raw_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Handle "Slide 1 Title:", "Title:", "제목:", etc.
            # Normalize: remove "Slide X" prefix if present
            clean_line = re.sub(r"^Slide \d+\s*", "", line, flags=re.IGNORECASE)
            
            if clean_line.startswith("Title:") or clean_line.startswith("제목:"):
                # Save previous slide
                if current_slide:
                    slides.append(current_slide)
                
                parts = clean_line.split(":", 1)
                if len(parts) > 1:
                    title_text = parts[1].strip()
                    current_slide = {'title': title_text, 'content': []}
                
            elif line.startswith("-") or line.startswith("•"):
                if current_slide:
                    bullet_text = line.lstrip("-• ").strip()
                    current_slide['content'].append(bullet_text)
            else:
                 # Support multi-line bullets or intro text (skip if no slide yet)
                 if current_slide:
                     current_slide['content'].append(line)

        if current_slide:
            slides.append(current_slide)
            
        return slides

    def generate_email_summary(self, prompt):
        """
        Generates a short email body summary.
        """
        return self.generate_report(prompt)

    def _wait_for_answer(self, page):
        """
        Waits for the answer to be generated and returns the text.
        """
        deadline = time.time() + 120 # 2 mins timeout
        last_text = ""
        stable_count = 0
        
        while time.time() < deadline:
             # Check if thinking
            try:
                thinking = page.locator(".thinking-message, [aria-label='Thinking']")
                if thinking.count() > 0 and thinking.first.is_visible():
                    time.sleep(1)
                    continue
            except:
                pass
            
            # extract text from latest message
            # The structure is usually a list of messages. We want the last one that is NOT from user.
            # Using RESPONSE_SELECTORS from config might be safer, but let's try to be generic.
            
            try:
                # Find all message contents
                # NotebookLM specific: .message-content or similar
                # We reuse RESPONSE_SELECTORS from config
                
                elements = page.locator(".model-response-text, .message-content, [data-message-author='model']")
                
                if elements.count() > 0:
                    latest = elements.last
                    text = latest.inner_text().strip()
                    
                    if text and text == last_text:
                        stable_count += 1
                        if stable_count >= 5: # Stable for 5 seconds
                            return text
                    else:
                        last_text = text
                        stable_count = 0
            except:
                pass
                
            time.sleep(1)
            
        print("[Reporter] Timeout waiting for answer")
        return None
