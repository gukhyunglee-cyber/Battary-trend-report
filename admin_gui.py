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
    layout="centered"
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
st.caption("모바일 관리 센터")

# Load initial data
if "config" not in st.session_state:
    with st.spinner("동기화 중..."):
        st.session_state.config = load_config_from_github()

if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

conf = st.session_state.config

# Mobile-friendly Tabs
tab1, tab2, tab3 = st.tabs(["👥 수신인", "🌐 사이트", "⚙️ 설정"])

# 모바일에서 컬럼 가로 배치 강제
st.markdown("""
    <style>
    /* 가로 스크롤 완전 차단 */
    html, body, [data-testid="stAppViewContainer"], .main {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    /* 제목 스타일 커스텀 */
    .custom-header {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        margin-right: 10px !important;
    }
    /* 버튼 정렬 */
    div[data-testid="column"] {
        display: flex !important;
        justify-content: flex-start !important;
    }
    /* 버튼 패딩 축소 */
    div[data-testid="stPopover"] > button {
        padding: 2px 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Tab 1: Recipients ---
with tab1:
    header_col, add_col, empty_col = st.columns([2, 2, 6])
    with header_col:
        st.markdown('<div class="custom-header">수신인</div>', unsafe_allow_html=True)
    with add_col:
        with st.popover("➕"):
            new_email = st.text_input("이메일 입력")
            if st.button("추가", use_container_width=True, type="primary"):
                if "@" in new_email:
                    recipients_list = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
                    recipients_list.append(new_email.strip())
                    conf["EMAIL_RECIPIENT"] = ", ".join(recipients_list)
                    st.session_state.config = conf
                    st.success("추가 완료!")
                    st.rerun()

    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    
    for i, email in enumerate(recipients):
        with st.expander(f"👤 {email}"):
            if st.button("❌ 삭제하기", key=f"del_rec_{i}", type="primary", use_container_width=True):
                recipients.pop(i)
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
                st.session_state.config = conf
                st.rerun()

# --- Tab 2: Target Sites ---
with tab2:
    header_col2, add_col2, empty_col2 = st.columns([2, 2, 6])
    with header_col2:
        st.markdown('<div class="custom-header">사이트</div>', unsafe_allow_html=True)
    with add_col2:
        with st.popover("➕"):
            with st.form("add_site_form_v5"):
                s_name = st.text_input("사이트 이름")
                s_url = st.text_input("주소 (URL)")
                s_cat = st.selectbox("분류", ["업계 미디어", "설비업체", "대한민국 미디어", "리서치", "중국 동향", "기타"])
                if st.form_submit_button("등록하기", use_container_width=True):
                    if s_name and s_url:
                        sites_list = conf.get("TARGET_SITES", [])
                        sites_list.append({"name": s_name, "url": s_url, "category": s_cat})
                        conf["TARGET_SITES"] = sites_list
                        st.session_state.config = conf
                        st.success("등록 완료!")
                        st.rerun()

    sites = conf.get("TARGET_SITES", [])
    
    for i, site in enumerate(sites):
        with st.expander(f"🌐 {site['name']}"):
            st.caption(site['url'])
            if st.button("❌ 삭제하기", key=f"del_site_{i}", type="primary", use_container_width=True):
                sites.pop(i)
                conf["TARGET_SITES"] = sites
                st.session_state.config = conf
                st.rerun()

# --- Tab 3: 설정 ---
with tab3:
    st.subheader("시스템 설정")
    
    with st.container(border=True):
        st.write("🔑 **API 설정**")
        gemini_key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
        conf["GEMINI_API_KEY"] = gemini_key
    
    st.markdown("### 🚀 액션")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        if st.button("▶️실행", type="primary", use_container_width=True):
            g, repo_name = get_github_client()
            if g:
                try:
                    repo = g.get_repo(repo_name)
                    workflow = repo.get_workflow("weekly_report.yml")
                    workflow.create_dispatch("main")
                    st.success("OK")
                except Exception as e:
                    st.error("Error")

    with btn_col2:
        if st.button("💾저장", type="primary", use_container_width=True):
            with st.spinner(".."):
                if save_config_to_github(conf):
                    st.success("OK")
                else:
                    st.error("Fail")

    with btn_col3:
        if st.button("🔄동기화", use_container_width=True):
            del st.session_state.config
            st.rerun()

# Global Delete Confirmation (Fixed overlay style for mobile)
if st.session_state.delete_confirm:
    type, idx, val = st.session_state.delete_confirm
    with st.container(border=True):
        st.error(f"**정말 삭제하시겠습니까?**\n\n대상: {val}")
        c1, c2 = st.columns(2)
        if c1.button("삭제", type="primary", use_container_width=True):
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
        if c2.button("취소", use_container_width=True):
            st.session_state.delete_confirm = None
            st.rerun()

# Sidebar info
st.sidebar.caption(f"Ver 2.5 (Mobile Optimized)")
st.sidebar.write(f"Emails: {len(recipients)}")
st.sidebar.write(f"Sites: {len(sites)}")
