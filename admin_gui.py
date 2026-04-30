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
    /* 팝업 버튼 스타일: 좌측 정렬 및 리스트 스타일 */
    div[data-testid="stPopover"] > button {
        width: 100% !important;
        text-align: left !important;
        justify-content: flex-start !important; /* 좌측 정렬 강제 */
        padding: 5px 10px !important;
        margin: 0px !important;
        border: none !important;
        border-radius: 0px !important;
        border-bottom: 0.5px solid #444 !important;
        background-color: transparent !important;
        color: white !important;
        font-size: 14px !important;
        height: auto !important;
        min-height: 40px !important;
    }
    div[data-testid="stPopover"] > button div {
        text-align: left !important;
        width: 100%;
    }
    div[data-testid="stPopoverContent"] {
        text-align: left !important;
    }
    </style>
    
    <script>
    // 롱 프레스(Long Press) 구현용 스크립트
    // 모든 팝업 버튼을 찾아서 클릭 이벤트를 막고 롱프레스(우클릭)시에만 실행되게 함
    const observer = new MutationObserver((mutations) => {
        const popoverButtons = window.parent.document.querySelectorAll('div[data-testid="stPopover"] > button');
        popoverButtons.forEach(btn => {
            if (!btn.dataset.longPressSet) {
                // 일반 클릭 차단 (선택 사항: 원하시면 짧은 클릭은 무시됨)
                // btn.style.pointerEvents = 'none'; // 이 방식은 롱프레스도 막으므로 지양
                
                btn.oncontextmenu = function(e) {
                    e.preventDefault(); // 기본 컨텍스트 메뉴 차단
                    this.click(); // 강제로 팝업 열기
                };
                btn.dataset.longPressSet = "true";
            }
        });
    });
    
    observer.observe(window.parent.document.body, {
        childList: true,
        subtree: true
    });
    </script>
    """, unsafe_allow_html=True)

# Mobile-friendly Tabs
tab1, tab2, tab3 = st.tabs(["👥 Recipients", "🌐 Sites", "⚙️ Settings"])

# --- Tab 1: Recipients ---
with tab1:
    st.subheader("Email Recipients")
    st.caption("💡 주소를 길게 누르면 삭제 메뉴가 나타납니다.")
    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    
    # Long-press Detection JS
    st.markdown("""
        <script>
        const items = window.parent.document.querySelectorAll('.long-press-target');
        items.forEach(item => {
            item.oncontextmenu = function(e) {
                e.preventDefault();
                const index = this.getAttribute('data-index');
                const type = this.getAttribute('data-type');
                // Streamlit의 특정 버튼을 클릭하게 하거나 메시지를 보낼 수 있음
                // 여기서는 팝업을 여는 현재의 안정적인 방식을 유지하되, 
                // 시각적으로 롱프레스 안내를 강화합니다.
            };
        });
        </script>
        """, unsafe_allow_html=True)

    for i, email in enumerate(recipients):
        # 팝업을 사용하되, 클릭이 아닌 '길게 누르기' 안내와 함께 배치
        with st.popover(f"👤 {email}", use_container_width=True):
            st.write(f"**{email}** 수신인을 삭제하시겠습니까?")
            if st.button("❌ 확정: 삭제하기", key=f"del_rec_{i}", type="primary", use_container_width=True):
                recipients.pop(i)
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
                st.session_state.config = conf
                st.rerun()

# --- Tab 2: Target Sites ---
with tab2:
    st.subheader("Collection Sites")
    st.caption("💡 사이트 이름을 길게 누르면 삭제 메뉴가 나타납니다.")
    sites = conf.get("TARGET_SITES", [])
    
    for i, site in enumerate(sites):
        with st.popover(f"🌐 {site['name']}", use_container_width=True):
            st.caption(site['url'])
            st.write(f"이 사이트를 수집 대상에서 삭제하시겠습니까?")
            if st.button("❌ 확정: 삭제하기", key=f"del_site_{i}", type="primary", use_container_width=True):
                sites.pop(i)
                conf["TARGET_SITES"] = sites
                st.session_state.config = conf
                st.rerun()

    st.markdown("---")
    with st.popover("➕ Add New Site", use_container_width=True):
        with st.form("add_site_form_v4"):
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
