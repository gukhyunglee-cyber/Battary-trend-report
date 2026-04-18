import sys
import os
import time
from pathlib import Path

# Use local dependencies copied to the project root
from auth_manager import AuthManager
from browser_utils import BrowserFactory, StealthUtils
from patchright.sync_api import sync_playwright

class NotebookUploader:
    def __init__(self, notebook_url: str):
        self.notebook_url = notebook_url
        self.auth = AuthManager()

    def create_notebook(self, title: str) -> str:
        """Create a new notebook and return its URL"""
        if not self.auth.is_authenticated():
            raise Exception("Not authenticated. Please run auth setup first.")

        print(f"Creating new notebook: {title}...")
        
        with sync_playwright() as p:
            context = BrowserFactory.launch_persistent_context(p, headless=False)
            page = context.new_page()
            
            try:
                page.goto("https://notebooklm.google.com/", wait_until="domcontentloaded")
                
                # Click "New Notebook"
                # Selectors for the big card with plus icon or "New Notebook" text
                # Try multiple likely selectors
                print("Looking for 'New Notebook' button...")
                
                # 1. Try text based
                new_btn = page.locator("text='New Notebook'")
                if not new_btn.is_visible():
                    new_btn = page.locator("text='새 노트북'")
                
                # 2. Try generic class/structure if text fails
                if not new_btn.is_visible():
                     # The first tile in the grid is usually "New Notebook"
                     # It often has a distinct class or aria-label
                     new_btn = page.locator("div[role='button']").filter(has_text="New Notebook").first
                     if not new_btn.is_visible():
                         new_btn = page.locator("div[role='button']").filter(has_text="새 노트북").first

                if not new_btn.is_visible():
                    # Fallback: clicking the first card-like element which usually is 'New'
                    # Or try aria-label which is very reliable if known.
                    # As of late 2024/early 2025, it might be an element with "Create"
                    new_btn = page.locator(".notebook-grid-item.create-new") 
                
                if new_btn.is_visible():
                    new_btn.click()
                else:
                    # Last ditch: Click the first available button in the main area (often the FAB or New card)
                    # Coordinates click might be too risky.
                    # Let's assume one of the texts worked. If not, we print error.
                    print("Could not find 'New Notebook' button by text. Trying heuristic...")
                    # The "New" button is often a large rectangular div with a Plus icon.
                    # We can look for the plus icon svg
                    page.locator("mat-icon:has-text('add')").first.click()

                # Wait for navigation to new notebook
                # The URL pattern is /notebook/<ID>
                page.wait_for_url(r"https://notebooklm\.google\.com/notebook/.*", timeout=15000)
                
                # Rename if needed (NotebookLM usually gives "Untitled notebook")
                # Clicking the title triggers rename mode
                # title_el = page.locator("input.notebook-title") # dynamic
                # For now, let's just return the URL. Renaming is a nice to have.
                
                current_url = page.url
                print(f"Created notebook at: {current_url}")
                return current_url
                
            except Exception as e:
                print(f"Failed to create notebook: {e}")
                import traceback
                traceback.print_exc()
                raise
            finally:
                context.close()

    def upload_text(self, title: str, content: str):
        """Upload text as a source to the notebook"""
        if not self.auth.is_authenticated():
            raise Exception("Not authenticated. Please run auth setup first.")

        # Ensure we have a valid notebook URL
        if not self.notebook_url or "notebook/" not in self.notebook_url:
            print("Invalid notebook URL provided to uploader.")
            raise ValueError("Invalid notebook URL")

        print(f"Uploading '{title}' to {self.notebook_url}...")
        
        with sync_playwright() as p:
            context = BrowserFactory.launch_persistent_context(p, headless=False)
            page = context.new_page()
            
            try:
                # Wait for page load
                print(f"Waiting for notebook to load: {self.notebook_url}")
                page.wait_for_selector("textarea, div[role='tab']", timeout=30000)
                
                # Check for "Sources" (출처) tab and click it to ensure "Add link" button is visible
                print("Ensuring Sources tab is active...")
                sources_tab = page.locator("div[role='tab']").filter(has_text="출처").first
                if sources_tab.is_visible():
                    sources_tab.click()
                    time.sleep(1)
                
                # Check for login redirection
                if "accounts.google.com" in page.url:
                    print("Redirected to login page! Auth likely invalid.")
                    raise Exception("Auth failed - redirected to login")
                
                # 1. Click "Add source" 
                print("Looking for Add Source button...")
                
                menu_opened = False
                for attempt in range(3):
                    print(f"Attempting to open menu (Attempt {attempt+1}/3)...")
                    add_button = None
                    
                    # Try finding by role and name (accessible name)
                    # Prioritize "Add source" over "Source"
                    keywords = ["Add source", "소스 추가"] 
                    # Removed "Source" and "소스" from primary search to avoid false positives
                    
                    for kw in keywords:
                        try:
                            # first=True is not available on get_by_role directly but we can use .first property
                            # however, get_by_role returns a locator
                            btn = page.get_by_role("button", name=kw)
                            if btn.count() > 0 and btn.first.is_visible():
                                add_button = btn.first
                                print(f"Found button with name: {kw}")
                                break
                        except Exception as e:
                            print(f"Error checking verification for {kw}: {e}")
    
                    if not add_button:
                         # Fallback specific aria-labels if generic role search failed
                         add_button = page.locator("button[aria-label='Add source'], button[aria-label='소스 추가']").first
                    
                    if not add_button or not add_button.is_visible():
                         # Fallback: Check if there is a floating action button or main area button if empty
                         # Using filtered locator to ensure it's a button
                         add_button = page.locator("button").filter(has_text="Add source").first
                         if not add_button.is_visible():
                             add_button = page.locator("button").filter(has_text="소스 추가").first
                    
                    # Last fallback: "Source" / "소스" but only if we haven't found anything better
                    if not add_button or not add_button.is_visible():
                        print("Trying fallback keyword 'Source'...")
                        add_button = page.get_by_role("button", name="Source").first
                        if not add_button.is_visible():
                            add_button = page.get_by_role("button", name="소스").first

                    if add_button and add_button.is_visible():
                        # print(f"Clicking button: {add_button}") # Locator print is verbose
                        add_button.click()
                        time.sleep(2) # Wait for menu
                        
                        # Verify menu opened
                        # Check for presence of "Website" or "PDF" or "YouTube"
                        if (page.get_by_text("Website").is_visible() or 
                            page.get_by_text("웹사이트").is_visible() or 
                            page.get_by_text("PDF").is_visible() or
                            page.get_by_text("YouTube").is_visible()):
                            print("Menu opened successfully!")
                            menu_opened = True
                            break
                        else:
                            print("Menu did not appear. Retrying...")
                    else:
                        print("Could not find Add Source button.")
                        time.sleep(1)
                
                if not menu_opened:
                    raise Exception("Failed to open source menu")

                time.sleep(1)

                # 2. Select "Copied text"
                # This opens a modal or menu
                print("Selecting Text option...")
                
                # Check for "Copied text" or "복사한 텍스트"
                # Using a broad text match might be safer for menu items
                
                print("Waiting for menu options to appear...")
                # Do not wait for role='menuitem' as it might be missing
                # Instead wait for specific text options
                
                menu_keywords = ["Copied text", "복사한 텍스트", "텍스트", "Text", "복사", "Clipboard"]
                text_option = None
                
                # Check visible text elements
                for kw in menu_keywords:
                    # We use locator with has_text, filtering for visible elements
                    # We try specific tags like div, span, button, or just generic text
                    try:
                        # Try to find a specialized menu item class or just text
                        # Angular Material often uses mat-menu-item which implies role=menuitem but maybe not here
                        # We use a broad search: Any element with text, visible.
                        # We prefer elements that look interactive (button, div with classes)
                        
                        # Just get by text
                        loc = page.get_by_text(kw)
                        if loc.count() > 0:
                            # Iterate to find the right one (there might be multiple 'Text' strings)
                            # We pick the one that is visible and likely in a menu (high z-index? difficult to check)
                            # We just pick the first visible one
                            for i in range(loc.count()):
                                if loc.nth(i).is_visible():
                                    print(f"Found visible element with text '{kw}'")
                                    text_option = loc.nth(i)
                                    break
                    except Exception as e:
                        pass
                    
                    if text_option:
                        break

                if not text_option:
                     # Fallback: look for generic class names if known?
                     # Or try accessible names for buttons again
                     pass

                if text_option:
                    print(f"Clicking menu option: {text_option.inner_text()}")
                    # Use force=True to bypass cdk-overlay-backdrop interception if necessary
                    text_option.click(force=True)
                else:
                    print("Could not find 'Copied text' menu option by text. Dumping HTML.")
                    # Fallback click on coordinates? No, too risky.
                    raise Exception("Could not find 'Copied text' menu option")
                
                # 3. Paste Content
                print("Pasting content...")
                
                # Wait for dialog
                # The "Copied text" option opens a dialog
                try:
                    dialog = page.get_by_role("dialog")
                    dialog.wait_for(timeout=5000)
                    print("Found dialog")
                    text_area = dialog.locator("textarea").first
                except:
                    print("Could not find dialog, falling back to any textarea")
                    text_area = page.locator("textarea").filter(has_text="").last # Try the last one as it might be the top-most
                
                # Check if visible and enabled
                print("Waiting for textarea to be enabled...")
                text_area.wait_for(state="visible", timeout=10000)
                
                # Sometimes it takes a moment to become enabled
                for i in range(10):
                    if text_area.is_enabled():
                        break
                    page.wait_for_timeout(500)
                    
                if not text_area.is_enabled():
                     print("Textarea is not enabled, dumping HTML")
                     raise Exception("Textarea not enabled")

                text_area.fill(content)
                
                # 4. Click Insert
                print("Clicking Insert...")
                insert_button = None
                
                # Try multiple keywords for the confirmation button
                insert_keywords = ["Insert", "삽입", "Add", "추가", "Confirm", "확인", "등록"]
                
                for kw in insert_keywords:
                    btn = page.get_by_role("button", name=kw)
                    if btn.count() > 0 and btn.first.is_visible():
                        insert_button = btn.first
                        print(f"Found Insert button: {kw}")
                        break
                
                if not insert_button:
                     # Fallback specific text match
                     print("Trying fallback text matches for Insert...")
                     for kw in insert_keywords:
                         btn = page.get_by_text(kw, exact=True)
                         if btn.count() > 0 and btn.first.is_visible():
                             insert_button = btn.first
                             print(f"Found Insert button by text: {kw}")
                             break

                if insert_button:
                    insert_button.click(force=True)
                else:
                    print("Could not find Insert button. Dumping HTML.")
                    raise Exception("Insert button not found")
                
                # Wait for upload processing
                print("Waiting for upload to complete...")
                # We can wait for the modal to disappear or a new source to appear in the list
                time.sleep(5) 
                
                print("Upload successful!")
                
            except Exception as e:
                print(f"Failed to upload: {e}")
                if page:
                    print(f"Current URL: {page.url}")
                try:
                    page.screenshot(path="upload_error.png")
                    print("Saved screenshot to upload_error.png")
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    print("Saved HTML to debug_page.html")
                except:
                    pass
                raise
            finally:
                context.close()

    def download_studio_slides(self, output_path: str, force_new: bool = False):
        """Download PPT from Notebook Studio Slides"""
        if not self.auth.is_authenticated():
            raise Exception("Not authenticated. Please run auth setup first.")

        if not self.notebook_url or "notebook/" not in self.notebook_url:
            raise ValueError("Invalid notebook URL")

        print(f"[Slides] Checking Studio Slides at {self.notebook_url}...")
        
        with sync_playwright() as p:
            context = BrowserFactory.launch_persistent_context(p, headless=False)
            page = context.new_page()
            
            try:
                page.goto(self.notebook_url, wait_until="domcontentloaded")
                
                # Wait for notebook to load
                print("[Slides] Waiting for notebook UI...")
                page.wait_for_selector("textarea", timeout=30000)
                
                # 1. Ensure Studio panel/tab is open
                print("[Slides] Detecting Studio UI layout...")
                
                # Check if it's a tab-based UI (like in smaller viewports) by looking for the "스튜디오" tab
                studio_tab = page.locator("div[role='tab']").filter(has_text="스튜디오").first
                if not studio_tab.is_visible():
                    # Fallback to the old header or toggle if tab is not found
                    studio_tab = page.locator("header").filter(has_text="스튜디오").first

                if studio_tab.is_visible():
                    print("[Slides] Clicking Studio tab/header to activate view...")
                    studio_tab.click()
                    time.sleep(2)
                else:
                    print("[Slides] Could not clearly find Studio tab. Trying fallback toggle button...")
                    toggle_btn = page.locator("button[aria-label*='스튜디오 패널']").first
                    if toggle_btn.is_visible() and "열기" in toggle_btn.get_attribute("aria-label", timeout=1000):
                        toggle_btn.click()

                # Wait for studio content to load
                print("[Slides] Waiting for Studio content...")
                page.wait_for_timeout(3000) 
                
                # 2. Look for existing slide artifact
                # Artifact more buttons have class .artifact-more-button
                more_btn_selector = "button.artifact-more-button"
                
                artifacts_count = page.locator(more_btn_selector).count()
                print(f"[Slides] Found {artifacts_count} artifacts in Studio panel.")
                
                existing_slides = None
                if artifacts_count > 0 and not force_new:
                    # Filter for slides if multiple artifacts exist
                    # Typically slides have a distinct icon or "Slide Materials" title above them
                    # For now we take the first/latest one
                    existing_slides = page.locator(more_btn_selector).first

                if force_new:
                    print("[Slides] force_new=True: 소스 변경이 감지되어 새 슬라이드를 강제 생성합니다.")
                    if artifacts_count > 0:
                        print("[Slides] 기존 아티팩트 삭제 중...")
                        old_btn = page.locator(more_btn_selector).first
                        old_btn.scroll_into_view_if_needed()
                        old_btn.click(force=True)
                        page.wait_for_timeout(1000)
                        
                        del_btn = page.locator("button[role='menuitem']").filter(has_text="삭제").first
                        if del_btn.is_visible():
                            del_btn.click()
                            page.wait_for_timeout(2000) # wait for deletion
                            print("[Slides] 기존 아티팩트 삭제 완료.")
                        else:
                            print("[Slides] 삭제 버튼을 찾을 수 없음. 무시하고 진행...")
                            page.keyboard.press("Escape")
                            page.wait_for_timeout(500)
                
                # Check for existing slides again after potential deletion
                artifacts_count = page.locator(more_btn_selector).count()
                if artifacts_count > 0 and not force_new:
                    existing_slides = page.locator(more_btn_selector).first
                else:
                    existing_slides = None
                
                if not existing_slides or not existing_slides.is_visible():
                    print("[Slides] No visible slide artifact. Attempting to locate 'Slide Materials' button...")
                    
                    # Try finding the generation button
                    # Multiple possible selectors based on subagent findings
                    gen_btn = page.locator("div[role='button']").filter(has_text="슬라이드 자료").first
                    if not gen_btn.is_visible():
                        gen_btn = page.locator("div[aria-label='슬라이드 자료'][role='button']").first
                    
                    if gen_btn.is_visible():
                        print("[Slides] Found 'Slide Materials' button. Clicking...")
                        gen_btn.scroll_into_view_if_needed()
                        gen_btn.click()
                        print("[Slides] Clicked generate. Waiting for completion (can take 2 min)...")
                        
                        # Wait for the artifact more button to appear (since we deleted it or it initially never existed)
                        page.locator(more_btn_selector).first.wait_for(state="visible", timeout=120000)
                        page.wait_for_timeout(3000) # buffer for generation finish
                        
                        existing_slides = page.locator(more_btn_selector).first
                    else:
                        print("[Slides] Could not find 'Slide Materials' button in Studio list.")
                        raise Exception("Slide generation button not found")

                # 3. Click 'More' (더보기)
                print("[Slides] Opening options menu for latest slide...")
                existing_slides.scroll_into_view_if_needed()
                existing_slides.click(force=True)
                page.wait_for_timeout(2000) 
                
                # 4. Wait for menu and click PPT download
                print("[Slides] Triggering PPT download...")
                # Search for the menu item with the text
                # We use role=menuitem and filter for "PowerPoint" or "PPT" or "pptx"
                download_item = page.locator("button[role='menuitem']").filter(has_text="PowerPoint").first
                if not download_item.is_visible():
                    # Fallback to general download text if lang is different
                    download_item = page.locator("button[role='menuitem']").filter(has_text="다운로드").first
                
                if not download_item.is_visible():
                    print("[Slides] PPT download menu item not found. visible menu items:")
                    menu_items = page.locator("button[role='menuitem']")
                    for i in range(menu_items.count()):
                        print(f"  - {menu_items.nth(i).inner_text()}")
                    raise Exception("PPT download menu item not found")

                # Handle the download
                with page.expect_download() as download_info:
                    download_item.click()
                
                download = download_info.value
                download.save_as(output_path)
                print(f"[Slides] Successfully downloaded PPT to: {output_path}")
                return output_path
                
            except Exception as e:
                print(f"[Slides] Failed to download slides: {e}")
                if page:
                    page.screenshot(path="slides_download_error.png")
                    with open("slides_debug.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                raise
            finally:
                context.close()

if __name__ == "__main__":
    # Test with dummy data
    from settings import NOTEBOOK_ID
    # Construct URL (assuming ID is set, otherwise use a placeholder or ask user)
    url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}" if NOTEBOOK_ID else "https://notebooklm.google.com/"
    
    uploader = NotebookUploader(url)
    uploader.upload_text("Test Source", "This is a test source uploaded by the Python script.")
