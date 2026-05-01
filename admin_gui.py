import streamlit as st
import json
import os
from github import Github
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Battery Admin",
    page_icon="⚡",
    layout="centered"
)

# Configuration
CONFIG_FILE = "config.json"

def get_github_client():
    """Get GitHub client using secrets."""
    token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    if not token or not repo_name:
        st.error("GitHub Secrets (GITHUB_TOKEN, GITHUB_REPO)가 설정되지 않았습니다.")
        return None, None
    return Github(token), repo_name

def load_config():
    """Load config.json from GitHub repository."""
    g, repo_name = get_github_client()
    if not g: return {}
    try:
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(CONFIG_FILE)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception as e:
        st.warning("설정을 불러올 수 없습니다. 새로 시작하거나 파일을 확인하세요.")
        return {}

def save_config(new_config):
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
            repo.create_file(CONFIG_FILE, "Initial config", json_content)
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False

# --- UI Layout ---
st.title("\u26a1 Battery Admin")
st.caption("모바일 관리 센터")

# Load initial data
if "config" not in st.session_state:
    with st.spinner("동기화 중..."):
        st.session_state.config = load_config()

if "delete_confirm" not in st.session_state:
    st.session_state.delete_confirm = None

conf = st.session_state.config

# CSS for layout
st.markdown("""
    <style>
    /* 가로 스크롤 방지 및 모바일 최적화 */
    html, body, [data-testid="stAppViewContainer"], .main {
        overflow-x: hidden !important;
        max-width: 100vw !important;
    }
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    /* 제목 옆 버튼 밀착 */
    div[data-testid="column"] {
        display: flex !important;
        justify-content: flex-start !important;
        align-items: center !important;
    }
    /* 버튼 패딩 축소 */
    div[data-testid="stPopover"] > button {
        padding: 2px 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["👥 수신인", "🌐 사이트", "⚙️ 설정"])

# --- Tab 1: Recipients ---
with tab1:
    h_col, a_col, e_col = st.columns([2, 2, 6])
    with h_col:
        st.markdown("### 수신인")
    with a_col:
        with st.popover("➕"):
            new_email = st.text_input("이메일 입력")
            if st.button("추가", use_container_width=True, type="primary"):
                if "@" in new_email:
                    recipients_list = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
                    recipients_list.append(new_email.strip())
                    conf["EMAIL_RECIPIENT"] = ", ".join(recipients_list)
                    st.session_state.config = conf
                    st.rerun()

    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    for i, email in enumerate(recipients):
        with st.expander(f"👤 {email}"):
            if st.button("❌ 삭제하기", key=f"del_rec_{i}", type="primary", use_container_width=True):
                st.session_state.delete_confirm = ("email", i, email)
                st.rerun()

# --- Tab 2: Sites ---
with tab2:
    h_col2, a_col2, e_col2 = st.columns([2, 2, 6])
    with h_col2:
        st.markdown("### 사이트")
    with a_col2:
        with st.popover("➕"):
            with st.form("add_site_form"):
                s_name = st.text_input("사이트 이름")
                s_url = st.text_input("주소 (URL)")
                s_cat = st.selectbox("분류", ["업계 미디어", "설비업체", "대한민국 미디어", "리서치", "중국 동향", "기타"])
                if st.form_submit_button("등록하기", use_container_width=True):
                    if s_name and s_url:
                        sites_list = conf.get("TARGET_SITES", [])
                        sites_list.append({"name": s_name, "url": s_url, "category": s_cat})
                        conf["TARGET_SITES"] = sites_list
                        st.session_state.config = conf
                        st.rerun()

    sites = conf.get("TARGET_SITES", [])
    for i, site in enumerate(sites):
        with st.expander(f"🌐 {site['name']}"):
            st.caption(site['url'])
            st.info(f"분류: {site.get('category', '미지정')}")
            if st.button("❌ 삭제하기", key=f"del_site_{i}", type="primary", use_container_width=True):
                st.session_state.delete_confirm = ("site", i, site['name'])
                st.rerun()

# --- Tab 3: Settings ---
with tab3:
    st.subheader("시스템 설정")
    with st.container(border=True):
        st.write("🔑 **API 설정**")
        gemini_key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
        conf["GEMINI_API_KEY"] = gemini_key
    
    st.markdown("### 🚀 액션")
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("▶️ 실행", type="primary", use_container_width=True):
            g, rn = get_github_client()
            if g:
                try:
                    g.get_repo(rn).get_workflow("weekly_report.yml").create_dispatch("main")
                    st.success("시작됨!")
                except: st.error("실행 실패")
    with b2:
        if st.button("💾 저장", type="primary", use_container_width=True):
            if save_config(conf): st.success("저장 완료!")
    with b3:
        if st.button("🔄 동기화", use_container_width=True):
            del st.session_state.config
            st.rerun()

# Global Delete Confirmation
if st.session_state.delete_confirm:
    type_k, idx, val = st.session_state.delete_confirm
    with st.status("⚠️ 삭제 확인", expanded=True):
        st.write(f"정말 삭제하시겠습니까?\n\n**{val}**")
        c1, c2 = st.columns(2)
        if c1.button("확인", type="primary", use_container_width=True):
            if type_k == "email":
                recipients.pop(idx)
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
            else:
                sites.pop(idx)
                conf["TARGET_SITES"] = sites
            st.session_state.delete_confirm = None
            st.rerun()
        if c2.button("취소", use_container_width=True):
            st.session_state.delete_confirm = None
            st.rerun()

# Sidebar
st.sidebar.caption("Ver 2.9 (Stable)")
st.sidebar.write(f"수신인: {len(recipients)}명")
st.sidebar.write(f"사이트: {len(sites)}개")
