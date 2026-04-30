"""
Configuration for Battery Trend Reporter
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Load dynamic config if exists
PROJECT_ROOT = Path(__file__).parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
dynamic_config = {}
if CONFIG_PATH.exists():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            dynamic_config = json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")

# ── 10개 타겟 사이트 (배터리 제조공정·설비 특화) ──────────────────────────
DEFAULT_SITES = [
    # ── 업계 미디어·뉴스 (6곳) ──
    {
        "name": "Munro & Associates",
        "url": "https://www.leandesign.com",
        "rss_url": None,
        "category": "업계 미디어",
        "description": "배터리 팝 해체분석 전문. Lean Design 방식론으로 EV 배터리 제조 공정·원가·설계 최적화 인사이트 제공",
    },
    {
        "name": "Charged EVs",
        "url": "https://chargedevs.com",
        "rss_url": "https://chargedevs.com/feed/",
        "category": "업계 미디어",
        "description": "설비업체 CEO 인터뷰, 드라이 전극 코팅 시스템 납품 현황, 장비 스펙 단독 취재",
    },
    {
        "name": "Electrive",
        "url": "https://www.electrive.com",
        "rss_url": "https://www.electrive.com/feed/",
        "category": "업계 미디어",
        "description": "유럽발 Cell-to-Pack 공법, 독일·유럽 배터리 R&D 프로젝트 동향",
    },
    {
        "name": "Benchmark Minerals",
        "url": "https://source.benchmarkminerals.com",
        "rss_url": None,
        "category": "업계 미디어",
        "description": "드라이 전극 공법 NMP 솔벤트 제거: LG에너지솔루션·Tesla 경쟁 구도, 비용·기술 분석",
    },
    {
        "name": "Energy Storage News",
        "url": "https://www.energy-storage.news",
        "rss_url": "https://www.energy-storage.news/feed/",
        "category": "업계 미디어",
        "description": "BESS용 배터리 팩 제조 공정, 포메이션·에이징 설비 발주 동향 특화",
    },
    {
        "name": "PV Tech",
        "url": "https://www.pv-tech.org",
        "rss_url": "https://www.pv-tech.org/feed/",
        "category": "업계 미디어",
        "description": "ESS용 셀 포맷(46파이 포함) 제조 투자·공법 전환 뉴스",
    },
    # ── 설비업체 공식 뉴스 (2곳) ──
    {
        "name": "Dürr AG",
        "url": "https://www.durr.com/en/media",
        "rss_url": None,
        "category": "설비업체",
        "description": "X.Cellify DC 드라이코팅 시스템, 솔벤트프리 전극 생산 기술 제1 출처",
    },
    {
        "name": "디일렉 (TheElec)",
        "url": "https://thelec.kr",
        "rss_url": "https://thelec.kr/rss/allArticle.xml",
        "category": "대한민국 미디어",
        "description": "국내외 배터리 장비 및 소재 업체 공급망 소식에 가장 정통한 IT 전문 매체",
    },
    # ── 리서치·기관 (2곳) ──
    {
        "name": "피엔티 (PNT)",
        "url": "https://www.epnt.co.kr",
        "rss_url": None,
        "category": "설비업체",
        "description": "국내 최고 수준의 롤투롤(Roll-to-Roll) 기술 기반 이차전지 전극 공정 장비 제조사",
    },
    {
        "name": "씨아이에스 (CIS)",
        "url": "https://www.cisro.co.kr",
        "rss_url": None,
        "category": "설비업체",
        "description": "이차전지 전극 공정(Coater, Calender, Slitter 등) 생산 설비 및 고체전지 장비 제조사",
    },
    {
        "name": "원준 (ONEJOON)",
        "url": "http://www.onejoon.co.kr",
        "rss_url": None,
        "category": "설비업체",
        "description": "이차전지 양극재 및 음극재 생산용 열처리 장비(소성로) 설계 및 제조 전문기업",
    },
    {
        "name": "IDTechEx",
        "url": "https://www.idtechex.com/research",
        "rss_url": None,
        "category": "리서치",
        "description": "고체전지·드라이코팅·46파이 셀 포맷 차세대 제조 기술 리포트",
    },
    {
        "name": "CNEVPost",
        "url": "https://cnevpost.com/",
        "rss_url": "https://cnevpost.com/feed/",
        "category": "업계 미디어 / 중국",
        "description": "CATL, BYD 등 중국 배터리 제조사 및 윈도우(Lead Intelligent) 등 중국 핵심 장비 업체 동향",
    },
    {
        "name": "Batteries News",
        "url": "https://batteriesnews.com/",
        "rss_url": "https://batteriesnews.com/feed/",
        "category": "업계 미디어 / 글로벌",
        "description": "배터리 시장 최신 전문 뉴스와 주요 배터리 기기 및 장비 전시회/이벤트 정보",
    },
]

# Use dynamic config if available, otherwise use default
TARGET_SITES = dynamic_config.get("TARGET_SITES", DEFAULT_SITES)

# NotebookLM Settings
NOTEBOOK_NAME = dynamic_config.get("NOTEBOOK_NAME", "Battery Trend Report")
NOTEBOOK_ID = dynamic_config.get("NOTEBOOK_ID", "18b97295-4392-47b3-a23d-a1dda255147a")

# Email Settings
EMAIL_SENDER = os.getenv("EMAIL_SENDER", dynamic_config.get("EMAIL_SENDER", "gukhyungLee@gmail.com"))
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", dynamic_config.get("EMAIL_PASSWORD", "bfxg jypj igku gcos"))
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", dynamic_config.get("EMAIL_RECIPIENT", "emittion@naver.com, gh2143.lee@samsung.com, hyeran.2@samsung.com, junghyuk.kim@samsung.com, zlzlznzn.yoo@samsung.com"))

# Gemini API Settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", dynamic_config.get("GEMINI_API_KEY", ""))

# LM Studio Settings
LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", dynamic_config.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1"))
LM_STUDIO_API_KEY = os.getenv("LM_STUDIO_API_KEY", dynamic_config.get("LM_STUDIO_API_KEY", "sk-lm-wPPVbFqK:fivACRL9zYpyZpDnCd0E"))
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", dynamic_config.get("LM_STUDIO_MODEL", "google/gemma-4-e4b"))

# Default AI Provider ("gemini" or "lm_studio")
AI_PROVIDER = os.getenv("AI_PROVIDER", dynamic_config.get("AI_PROVIDER", "lm_studio"))
