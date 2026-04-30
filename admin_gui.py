import streamlit as st
import json
import os
from github import Github
import pandas as pd
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Battery Trend Admin",
    page_icon="⚡",
    layout="wide"
)

# Configuration
CONFIG_FILE = "config.json"

def get_github_client():
    """Get GitHub client using secrets."""
    token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO") # e.g. "username/battery-trend-report"
    if not token or not repo_name:
        st.error("GitHub Secrets (GITHUB_TOKEN, GITHUB_REPO)가 설정되지 않았습니다.")
        return None, None
    return Github(token), repo_name

def load_config_from_github():
    """Load config.json from GitHub repository."""
    g, repo_name = get_github_client()
    if not g: return {}
    
    try:
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(CONFIG_FILE)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception as e:
        st.warning(f"기존 설정을 불러올 수 없습니다 (새로 시작하거나 파일을 확인하세요): {e}")
        return {}

def save_config_to_github(new_config):
    """Save config.json back to GitHub."""
    g, repo_name = get_github_client()
    if not g: return False
    
    try:
        repo = g.get_repo(repo_name)
        json_content = json.dumps(new_config, indent=2, ensure_ascii=False)
        
        try:
            contents = repo.get_contents(CONFIG_FILE)
            repo.update_file(
                contents.path, 
                f"Update config via Admin UI ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
                json_content, 
                contents.sha
            )
        except:
            # File doesn't exist, create it
            repo.create_file(
                CONFIG_FILE,
                "Initial config via Admin UI",
                json_content
            )
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False

# --- UI Layout ---
st.title("⚡ Battery Trend Reporter 관리자")
st.markdown("모바일에서 간편하게 수신인과 수집 사이트를 관리하세요.")

# Load initial data
if "config" not in st.session_state:
    with st.spinner("깃허브에서 설정을 불러오는 중..."):
        st.session_state.config = load_config_from_github()

conf = st.session_state.config

# 1. Email Recipients Section
st.header("📧 수신인 관리")
current_recipients = conf.get("EMAIL_RECIPIENT", "")
new_recipients = st.text_area(
    "수신인 이메일 (쉼표 또는 줄바꿈으로 구분)",
    value=current_recipients.replace(", ", "\n"),
    height=150,
    help="리포트를 받을 사람들의 이메일을 입력하세요."
)
# Format back to comma-separated
formatted_recipients = ", ".join([r.strip() for r in new_recipients.split() if "@" in r])

# 2. Target Sites Section
st.header("🔗 수집 사이트 목록")
sites = conf.get("TARGET_SITES", [])
if not sites:
    st.info("수집 사이트 목록이 비어있습니다. 기본값이 사용됩니다.")

# Display as table for easy view
if sites:
    df = pd.DataFrame(sites)[["name", "url", "category"]]
    st.table(df)

# Add/Edit Sites (Simplified for mobile)
with st.expander("사이트 추가/수정"):
    st.info("현재는 JSON 직접 편집 기능을 제공합니다. (추후 UI 개선 가능)")
    sites_json = st.text_area("사이트 목록 (JSON)", value=json.dumps(sites, indent=2, ensure_ascii=False), height=300)
    try:
        updated_sites = json.loads(sites_json)
    except:
        st.error("JSON 형식이 올바르지 않습니다.")
        updated_sites = sites

# 3. API Keys Section
st.header("🔑 API 설정")
gemini_key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")

# --- Save Button ---
st.divider()
if st.button("💾 설정 저장하기 (GitHub에 반영)", type="primary"):
    new_data = {
        "EMAIL_RECIPIENT": formatted_recipients,
        "TARGET_SITES": updated_sites,
        "GEMINI_API_KEY": gemini_key,
        "AI_PROVIDER": "gemini",
        "NOTEBOOK_NAME": conf.get("NOTEBOOK_NAME", "Battery Trend Report"),
        "NOTEBOOK_ID": conf.get("NOTEBOOK_ID", "18b97295-4392-47b3-a23d-a1dda255147a")
    }
    
    with st.spinner("깃허브에 저장 중..."):
        if save_config_to_github(new_data):
            st.success("✅ 설정이 저장되었습니다! 다음 리포트 실행 시 반영됩니다.")
            st.session_state.config = new_data
        else:
            st.error("❌ 저장에 실패했습니다. 깃허브 토큰 설정을 확인하세요.")

# --- Workflow Trigger ---
st.sidebar.header("🚀 작업 실행")
if st.sidebar.button("지금 즉시 리포트 생성"):
    st.sidebar.warning("이 기능은 GitHub Actions API 연동이 필요합니다. (준비 중)")
    # TODO: Add workflow_dispatch trigger logic
