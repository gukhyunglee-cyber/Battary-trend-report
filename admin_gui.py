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
st.title("⚡ Battery Admin")
st.caption("Mobile-optimized Control Center")

# Load initial data
if "config" not in st.session_state:
    with st.spinner("Syncing..."):
        st.session_state.config = load_config_from_github()

if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

conf = st.session_state.config

# Force ultra-compact layout on mobile via CSS
st.markdown("""
    <style>
    /* 전체 앱 여백 최소화 */
    .block-container {
        padding: 0.5rem !important;
        max-width: 100% !important;
    }
    /* 리스트 버튼 스타일: 배경/테두리 제거 및 간격 최소화 */
    div.stButton > button {
        width: 100% !important;
        text-align: left !important;
        padding: 2px 5px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        border-bottom: 0.5px solid #444 !important; /* 구분선 */
        background-color: transparent !important;
        color: white !important;
        font-size: 14px !important;
        height: auto !important;
        min-height: 32px !important;
    }
    div.stButton > button:hover {
        background-color: #333 !important;
    }
    /* 탭 간격 조정 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Mobile-friendly Tabs
tab1, tab2, tab3 = st.tabs(["👥 Recipients", "🌐 Sites", "⚙️ Settings"])

# --- Tab 1: Recipients ---
with tab1:
    st.subheader("Email Recipients")
    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    
    for i, email in enumerate(recipients):
        if st.button(f"👤 {email}", key=f"rec_btn_{i}"):
            st.session_state.delete_confirm = ("email", i, email)

    st.markdown("---")
    with st.popover("➕ Add New Recipient", use_container_width=True):
        new_email = st.text_input("Enter Email")
        if st.button("Add Now", use_container_width=True, type="primary"):
            if "@" in new_email:
                recipients.append(new_email.strip())
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
                st.success("Added!")
                st.rerun()

# --- Tab 2: Target Sites ---
with tab2:
    st.subheader("Collection Sites")
    sites = conf.get("TARGET_SITES", [])
    
    for i, site in enumerate(sites):
        if st.button(f"🌐 {site['name']} ({site['url']})", key=f"site_btn_{i}"):
            st.session_state.delete_confirm = ("site", i, site['name'])

    st.markdown("---")
    with st.popover("➕ Add New Site", use_container_width=True):
        with st.form("add_site_form_v3"):
            s_name = st.text_input("Site Name")
            s_url = st.text_input("URL")
            s_cat = st.selectbox("Category", ["업계 미디어", "설비업체", "대한민국 미디어", "리서치", "중국 동향", "기타"])
            if st.form_submit_button("Register Site", use_container_width=True):
                if s_name and s_url:
                    sites.append({"name": s_name, "url": s_url, "category": s_cat})
                    conf["TARGET_SITES"] = sites
                    st.success("Registered!")
                    st.rerun()

# --- Tab 3: Settings ---
with tab3:
    st.subheader("System Settings")
    
    with st.container(border=True):
        st.write("🔑 **API Configuration**")
        gemini_key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
        conf["GEMINI_API_KEY"] = gemini_key
    
    st.markdown("### 🚀 Actions")
    if st.button("💾 SAVE ALL TO GITHUB", type="primary", use_container_width=True):
        with st.spinner("Uploading..."):
            if save_config_to_github(conf):
                st.success("Successfully Saved!")
            else:
                st.error("Save Failed")

    if st.button("🔄 Sync with Cloud", use_container_width=True):
        del st.session_state.config
        st.rerun()

# Global Delete Confirmation (Fixed overlay style for mobile)
if st.session_state.delete_confirm:
    type, idx, val = st.session_state.delete_confirm
    with st.container(border=True):
        st.error(f"**Confirm Deletion?**\n\nTarget: {val}")
        c1, c2 = st.columns(2)
        if c1.button("YES", type="primary", use_container_width=True):
            if type == "email":
                recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
                recipients.pop(idx)
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
            else:
                sites = conf.get("TARGET_SITES", [])
                sites.pop(idx)
                conf["TARGET_SITES"] = sites
            st.session_state.delete_confirm = None
            st.rerun()
        if c2.button("NO", use_container_width=True):
            st.session_state.delete_confirm = None
            st.rerun()

# Sidebar info
st.sidebar.caption(f"Ver 2.0 (Mobile Optimized)")
st.sidebar.write(f"Emails: {len(recipients)}")
st.sidebar.write(f"Sites: {len(sites)}")
