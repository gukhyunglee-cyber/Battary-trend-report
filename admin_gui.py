import streamlit as st
import json
from github import Github
from datetime import datetime

# Page config
st.set_page_config(page_title="Battery Admin", page_icon="⚡", layout="centered")

# --- CSS: Extreme Layout Stabilization ---
st.markdown("""
<style>
    /* 1. 전역 가로 스크롤 절대 차단 */
    html, body, [data-testid="stAppViewContainer"], .main { 
        max-width: 100vw !important;
        overflow-x: hidden !important;
        position: fixed; /* 화면 고정 */
        width: 100%;
        height: 100%;
    }
    .main .block-container { 
        padding: 1rem 0.5rem !important; 
        max-width: 100% !important;
        overflow-y: auto !important; /* 세로 스크롤만 허용 */
        height: 100vh;
    }
    
    /* 2. 헤더 & ➕ 버튼 강제 밀착 */
    .header-container {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 10px !important;
        margin-bottom: 10px !important;
        width: 100% !important;
    }
    .custom-header {
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
        color: #E0E0F0 !important;
    }

    /* 3. 설정 버튼 (Tab 3) 압축 */
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_"]) {
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 2px !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_"]) > div[data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_"]) button {
        padding: 4px 0 !important;
        font-size: 0.7rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- GitHub Logic ---
def get_github():
    t, r = st.secrets.get("GITHUB_TOKEN"), st.secrets.get("GITHUB_REPO")
    if not t or not r: return None, None
    return Github(t), r

def load_config():
    g, rn = get_github()
    if not g: return {}
    try:
        repo = g.get_repo(rn)
        return json.loads(repo.get_contents("config.json").decoded_content.decode("utf-8"))
    except: return {}

def save_config(cfg):
    g, rn = get_github()
    if not g: return False
    try:
        repo = g.get_repo(rn)
        c = repo.get_contents("config.json")
        repo.update_file(c.path, "Update via UI", json.dumps(cfg, indent=2, ensure_ascii=False), c.sha)
        return True
    except: return False

def get_file_content(filename):
    g, rn = get_github()
    if not g: return "GitHub 연동 오류"
    try:
        repo = g.get_repo(rn)
        return repo.get_contents(filename).decoded_content.decode("utf-8")
    except: return "파일 내용을 불러올 수 없습니다."

# --- App State ---
if "config" not in st.session_state:
    with st.spinner("Loading..."): st.session_state.config = load_config()
if "current_report" not in st.session_state:
    st.session_state.current_report = ""

conf = st.session_state.config

# --- App Content ---
st.title("⚡ Battery Admin")
st.caption("모바일 관리 센터")

tab1, tab2, tab3, tab4 = st.tabs(["👥 수신인", "🌐 사이트", "⚙️ 설정", "📝 리포트"])

# --- Tab 1: Recipients ---
with tab1:
    # Use HTML for better alignment control
    st.markdown('<div class="header-container"><div class="custom-header">수신인</div>', unsafe_allow_html=True)
    with st.popover("➕"):
        email = st.text_input("이메일")
        if st.button("추가", key="add_email", type="primary", use_container_width=True):
            if "@" in email:
                rl = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
                rl.append(email.strip())
                conf["EMAIL_RECIPIENT"] = ", ".join(rl)
                st.session_state.config = conf
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    for i, r in enumerate(recipients):
        with st.expander(f"👤 {r}"):
            if st.button("❌ 삭제", key=f"del_r_{i}", type="primary", use_container_width=True):
                recipients.pop(i)
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
                st.rerun()

# --- Tab 2: Sites ---
with tab2:
    st.markdown('<div class="header-container"><div class="custom-header">사이트</div>', unsafe_allow_html=True)
    with st.popover("➕"):
        with st.form("add_site"):
            n = st.text_input("이름")
            u = st.text_input("URL")
            cat = st.selectbox("분류", ["업계 미디어", "설비업체", "기타"])
            if st.form_submit_button("등록", use_container_width=True):
                sl = conf.get("TARGET_SITES", [])
                sl.append({"name": n, "url": u, "category": cat})
                conf["TARGET_SITES"] = sl
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    sites = conf.get("TARGET_SITES", [])
    for i, s in enumerate(sites):
        with st.expander(f"🌐 {s['name']}"):
            st.caption(s['url'])
            if st.button("❌ 삭제", key=f"del_s_{i}", type="primary", use_container_width=True):
                sites.pop(i)
                conf["TARGET_SITES"] = sites
                st.rerun()

# --- Tab 3: Settings ---
with tab3:
    st.subheader("시스템 설정")
    key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
    conf["GEMINI_API_KEY"] = key
    
    st.markdown("### 🚀 액션")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        if st.button("실행", key="btn_run", use_container_width=True):
            g, rn = get_github()
            if g:
                try: 
                    g.get_repo(rn).get_workflow("weekly_report.yml").create_dispatch("main")
                    st.success("OK")
                except: st.error("ERR")
    with sc2:
        if st.button("저장", key="btn_save", use_container_width=True):
            if save_config(conf): st.success("OK")
    with sc3:
        if st.button("동기", key="btn_sync", use_container_width=True):
            del st.session_state.config
            st.rerun()

# --- Tab 4: Reports ---
with tab4:
    st.subheader("📝 최근 발신 리포트")
    report_type = st.radio("종류 선택", ["주간 분석 요약", "트렌드 리포트"], horizontal=True)
    target_file = "weekly_diff_report.md" if report_type == "주간 분석 요약" else "trend_report.md"
    
    if st.button("리포트 불러오기"):
        with st.spinner("가져오는 중..."):
            st.session_state.current_report = get_file_content(target_file)
    
    if st.session_state.current_report:
        st.markdown("---")
        st.markdown(st.session_state.current_report)

st.sidebar.caption("Ver 3.6 (Stable UI)")
st.sidebar.write(f"수신인: {len(recipients)}명")
st.sidebar.write(f"사이트: {len(sites)}개")
