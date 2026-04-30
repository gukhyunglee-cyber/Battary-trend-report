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
st.title("⚡ Battery Trend Admin Center")
st.markdown("전용 관리자 패널에서 리포트 설정을 실시간으로 제어하세요.")

# Load initial data
if "config" not in st.session_state:
    with st.spinner("깃허브에서 최신 설정을 동기화 중..."):
        st.session_state.config = load_config_from_github()

if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

conf = st.session_state.config

# --- 1. Email Recipients Section ---
st.header("📧 수신인 관리")

# Current Recipients List
recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]

for i, email in enumerate(recipients):
    cols = st.columns([4, 1])
    cols[0].write(f"**{i+1}.** {email}")
    if cols[1].button("삭제", key=f"del_email_{i}"):
        st.session_state.delete_confirm = ("email", i, email)

# Email Delete Confirmation
if st.session_state.delete_confirm and st.session_state.delete_confirm[0] == "email":
    type, idx, val = st.session_state.delete_confirm
    st.warning(f"정말 '{val}' 수신인을 삭제하시겠습니까?")
    c1, c2 = st.columns(2)
    if c1.button("확인(삭제)", type="primary"):
        recipients.pop(idx)
        conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
        st.session_state.delete_confirm = None
        st.rerun()
    if c2.button("취소"):
        st.session_state.delete_confirm = None
        st.rerun()

# Add Email Popover
with st.popover("➕ 수신인 추가"):
    new_email = st.text_input("새 이메일 주소")
    if st.button("등록하기"):
        if "@" in new_email:
            recipients.append(new_email.strip())
            conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
            st.success("추가되었습니다!")
            st.rerun()
        else:
            st.error("유효한 이메일 형식이 아닙니다.")

st.divider()

# --- 2. Target Sites Section ---
st.header("🔗 수집 사이트 관리")

sites = conf.get("TARGET_SITES", [])

# Display sites with delete buttons
for i, site in enumerate(sites):
    with st.container(border=True):
        cols = st.columns([3, 1, 1])
        cols[0].write(f"**{site['name']}**")
        cols[0].caption(site['url'])
        cols[1].info(site.get('category', '미분류'))
        if cols[2].button("삭제", key=f"del_site_{i}"):
            st.session_state.delete_confirm = ("site", i, site['name'])

# Site Delete Confirmation
if st.session_state.delete_confirm and st.session_state.delete_confirm[0] == "site":
    type, idx, val = st.session_state.delete_confirm
    st.warning(f"정말 '{val}' 사이트를 수집 대상에서 삭제하시겠습니까?")
    c1, c2 = st.columns(2)
    if c1.button("확인(삭제)", type="primary", key="confirm_site_del"):
        sites.pop(idx)
        conf["TARGET_SITES"] = sites
        st.session_state.delete_confirm = None
        st.rerun()
    if c2.button("취소", key="cancel_site_del"):
        st.session_state.delete_confirm = None
        st.rerun()

# Add Site Popover
with st.popover("➕ 새 수집 사이트 추가"):
    with st.form("add_site_form"):
        s_name = st.text_input("사이트 이름 (예: 테슬라 뉴스)")
        s_url = st.text_input("URL (https://...)")
        s_cat = st.selectbox("카테고리", ["업계 미디어", "설비업체", "대한민국 미디어", "리서치", "중국 동향", "기타"])
        
        if st.form_submit_button("사이트 등록"):
            if s_name and s_url.startswith("http"):
                new_site = {"name": s_name, "url": s_url, "category": s_cat}
                sites.append(new_site)
                conf["TARGET_SITES"] = sites
                st.success("사이트가 목록에 추가되었습니다!")
                st.rerun()
            else:
                st.error("이름과 올바른 URL을 입력하세요.")

# --- Save & API Section ---
st.divider()
st.header("⚙️ 최종 설정 및 저장")

with st.expander("🔑 API 키 관리"):
    gemini_key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
    conf["GEMINI_API_KEY"] = gemini_key

if st.button("💾 모든 변경 사항 GitHub에 저장", type="primary", use_container_width=True):
    with st.spinner("깃허브 서버와 동기화 중..."):
        if save_config_to_github(conf):
            st.success("✅ 모든 변경 사항이 깃허브에 영구 저장되었습니다!")
        else:
            st.error("❌ 저장 실패. 설정을 확인해 주세요.")

# Sidebar status
st.sidebar.title("📊 시스템 상태")
st.sidebar.info(f"수신인: {len(recipients)}명")
st.sidebar.info(f"수집 사이트: {len(sites)}곳")
if st.sidebar.button("새로고침(동기화)"):
    del st.session_state.config
    st.rerun()
