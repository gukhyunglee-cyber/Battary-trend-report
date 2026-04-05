"""
Configuration for Battery Trend Reporter
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Search Settings
SEARCH_KEYWORDS_KR = ["2차전지 최신 이슈", "배터리 업계 동향", "2차전지 전시회 일정", "배터리 박람회 참가 업체"]
SEARCH_KEYWORDS_EN = ["Secondary Battery Trends", "Battery Industry News", "Battery Exhibitions 2024 2025"]

# YouTube Settings
YOUTUBE_KEYWORDS = ["2차전지 이슈", "배터리 기술 동향"]

# NotebookLM Settings
NOTEBOOK_NAME = "Battery Trend Report"
# Notebook ID will be determined dynamically or set here after creation
NOTEBOOK_ID = "18b97295-4392-47b3-a23d-a1dda255147a" 

# Email Settings
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "gukhyungLee@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "bfxg jypj igku gcos")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "emittion@naver.com, gh2143.lee@samsung.com, hyeran.2@samsung.com, junghyuk.kim@samsung.com")

# Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

