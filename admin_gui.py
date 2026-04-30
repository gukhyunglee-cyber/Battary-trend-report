import streamlit as st
import json
import os
from github import Github
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
    token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    if not token or not repo_name:
        return None, None
    return Github(token), repo_name

def load_config_from_github():
    g, repo_name = get_github_client()
    if not g: return {}
    try:
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(CONFIG_FILE)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception:
        return {}

def save_config_to_github(new_config):
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
            repo.create_file(CONFIG_FILE, "Initial config via Admin UI", json_content)
        return True
    except Exception:
        return False

# --- UI Header ---
st.title("⚡ Battery Admin")
st.caption("Mobile-optimized Control Center v2.5")

# CSS: Ensure visibility and left alignment
st.markdown("""
    <style>
    /* 상단 여백 확보하여 제목 가림 방지 */
    .block-container {
        padding-top: 3rem !important;
        padding-bottom: 2rem !important;
        max-width: 100% !important;
    }
    /* 컬럼 컨테이너 줄바꿈 해제 및 좌우 정렬 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    div[data-testid="column"]:nth-of-type(1) {
        flex: 1 1 auto !important;
        min-width: 0px !important;
        text-align: left !important;
    }
    div[data-testid="column"]:nth-of-type(2) {
        flex: 0 0 45px !important;
        min-width: 45px !important;
        text-align: right !important;
    }
    /* 버튼 스타일 */
    .stButton > button {
        width: 35px !important;
        height: 35px !important;
        padding: 0px !important;
    }
    /* 탭 간격 최적화 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# Load data
if "config" not in st.session_state:
    st.session_state.config = load_config_from_github()

conf = st.session_state.config

# Mobile Tabs
tab1, tab2, tab3 = st.tabs(["👥 Recipients", "🌐 Sites", "⚙️ Settings"])

# --- Tab 1: Recipients ---
with tab1:
    st.subheader("Email Recipients")
    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    
    for i, email in enumerate(recipients):
        cols = st.columns([10, 1])
        cols[0].markdown(f'<div style="text-align:left; font-size:14px; padding:5px 0;">{email}</div>', unsafe_allow_html=True)
        if cols[1].button("🗑️", key=f"del_rec_btn_{i}"):
            st.session_state.delete_confirm = ("email", i, email)
        st.divider()

    st.markdown("---")
    with st.popover("➕ Add New Recipient", use_container_width=True):
        new_email = st.text_input("Enter Email")
        if st.button("Add Now", use_container_width=True, type="primary"):
            if "@" in new_email:
                recipients.append(new_email.strip())
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
                st.session_state.config = conf
                st.success("Added!")
                st.rerun()

# --- Tab 2: Target Sites ---
with tab2:
    st.subheader("Collection Sites")
    sites = conf.get("TARGET_SITES", [])
    
    for i, site in enumerate(sites):
        cols = st.columns([10, 1])
        with cols[0]:
            st.markdown(f'<div style="text-align:left; font-size:14px;"><b>{site["name"]}</b></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="text-align:left; font-size:11px; color:#888;">{site["url"]}</div>', unsafe_allow_html=True)
        if cols[1].button("🗑️", key=f"del_site_btn_{i}"):
            st.session_state.delete_confirm = ("site", i, site['name'])
        st.divider()

    st.markdown("---")
    with st.popover("➕ Add New Site", use_container_width=True):
        with st.form("add_site_form_v5"):
            s_name = st.text_input("Site Name")
            s_url = st.text_input("URL")
            s_cat = st.selectbox("Category", ["업계 미디어", "설비업체", "대한민국 미디어", "리서치", "중국 동향", "기타"])
            if st.form_submit_button("Register Site", use_container_width=True):
                if s_name and s_url:
                    sites.append({"name": s_name, "url": s_url, "category": s_cat})
                    conf["TARGET_SITES"] = sites
                    st.session_state.config = conf
                    st.success("Added locally!")
                    st.rerun()

# --- Tab 3: Settings ---
with tab3:
    st.subheader("System Settings")
    
    with st.container(border=True):
        st.write("🔑 **Gemini API Key**")
        gemini_key = st.text_input("API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
        conf["GEMINI_API_KEY"] = gemini_key
    
    st.markdown("### 💾 GitHub Cloud Save")
    st.info("수정한 내용을 깃허브에 반영하려면 아래 버튼을 꼭 누르세요.")
    if st.button("🚀 SAVE ALL TO GITHUB", type="primary", use_container_width=True):
        if save_config_to_github(conf):
            st.success("GitHub에 저장 완료!")
        else:
            st.error("저장 실패 (비밀번호/권한 확인)")

# Sidebar Summary
st.sidebar.title("Summary")
st.sidebar.write(f"Recipients: {len(recipients)}")
st.sidebar.write(f"Sites: {len(sites)}")
st.sidebar.caption("Last Synced: " + datetime.now().strftime("%H:%M:%S"))
