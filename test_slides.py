import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from uploader import NotebookUploader
from settings import NOTEBOOK_ID

def test_download():
    if not NOTEBOOK_ID:
        print("Error: NOTEBOOK_ID not found in settings.py")
        return

    url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"
    uploader = NotebookUploader(url)
    
    output_file = os.path.join(os.getcwd(), "test_studio_slides.pptx")
    print(f"Testing Slide Download to: {output_file}")
    
    try:
        uploader.download_studio_slides(output_file)
        if os.path.exists(output_file):
            print(f"SUCCESS: File downloaded ({os.path.getsize(output_file)} bytes)")
        else:
            print("FAILURE: File not found after download attempt")
    except Exception as e:
        print(f"ERROR during download: {e}")

if __name__ == "__main__":
    test_download()
