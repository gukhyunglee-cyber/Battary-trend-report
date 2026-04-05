
import re

def analyze_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # adjust regex to catch aria-label
    aria_labels = re.findall(r'aria-label="([^"]+)"', content)
    # Print ALL aria-labels to see menu items
    print("All aria-labels:")
    for label in aria_labels:
        print(f" - {label}")

    placeholders = re.findall(r'placeholder="([^"]+)"', content)
    print("Found placeholders:", len(placeholders))
    for ph in placeholders:
        print(f" - {ph}")
        
    # Search for menu related text
    keywords = ["Text", "Copied", "복사", "텍스트", "PDF", "Website", "웹사이트", "YouTube", "Source"]
    for kw in keywords:
        if kw in content:
            print(f"Found keyword '{kw}'")
        else:
            print(f"Keyword '{kw}' NOT found")
        
analyze_html(r"c:\Users\82106\OneDrive\바탕 화면\python_workplace\battery-trend-reporter\debug_page.html")
