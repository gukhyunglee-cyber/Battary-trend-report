import streamlit as st
import json
from github import Github
from datetime import datetime

st.set_page_config(
    page_title="⚡ Battery Admin",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CONFIG_FILE = "config.json"


def get_github_client():
    token = st.secrets.get("GITHUB_TOKEN")
    repo_name = st.secrets.get("GITHUB_REPO")
    if not token or not repo_name:
        st.error("GitHub Secrets 미설정 (GITHUB_TOKEN, GITHUB_REPO)")
        return None, None
    return Github(token), repo_name


def load_config():
    g, repo_name = get_github_client()
    if not g:
        return {}
    try:
        repo = g.get_repo(repo_name)
        contents = repo.get_contents(CONFIG_FILE)
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception as e:
        st.warning(f"설정 로드 실패: {e}")
        return {}


def save_config(cfg):
    g, repo_name = get_github_client()
    if not g:
        return False
    try:
        repo = g.get_repo(repo_name)
        content = json.dumps(cfg, indent=2, ensure_ascii=False)
        try:
            f = repo.get_contents(CONFIG_FILE)
            repo.update_file(
                f.path,
                f"Config update ({datetime.now().strftime('%Y-%m-%d %H:%M')})",
                content,
                f.sha,
            )
        except Exception:
            repo.create_file(CONFIG_FILE, "Initial config", content)
        return True
    except Exception as e:
        st.error(f"저장 실패: {e}")
        return False


# ── Design System ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ===== BASE ===== */
html, body, [data-testid="stAppViewContainer"], .main {
    background: #07070F !important;
    color: #E0E0F0 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif !important;
    overflow-x: hidden !important;
    max-width: 100vw !important;
}
.main .block-container {
    padding: 0.6rem 0.85rem 1.5rem !important;
    max-width: 480px !important;
    margin: 0 auto !important;
}

/* ===== HIDE STREAMLIT CHROME ===== */
#MainMenu, footer, header, .stDeployButton { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ===== APP HEADER ===== */
.app-header {
    display: flex;
    align-items: center;
    padding: 10px 0 12px;
    border-bottom: 1px solid rgba(0, 255, 157, 0.12);
    margin-bottom: 12px;
    gap: 7px;
}
.app-logo { font-size: 1.25rem; }
.app-name {
    font-size: 1.1rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00FF9D 0%, #00D1FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.3px;
    flex: 1;
}
.app-ver {
    font-size: 0.58rem;
    color: rgba(0, 255, 157, 0.45);
    border: 1px solid rgba(0, 255, 157, 0.18);
    border-radius: 20px;
    padding: 2px 8px;
    background: rgba(0, 255, 157, 0.04);
    white-space: nowrap;
}

/* ===== STATS ROW ===== */
.stats-row {
    display: flex;
    gap: 7px;
    margin-bottom: 13px;
}
.stat-box {
    flex: 1;
    background: rgba(255, 255, 255, 0.035);
    border: 1px solid rgba(255, 255, 255, 0.065);
    border-radius: 12px;
    padding: 9px 6px 8px;
    text-align: center;
    transition: border-color 0.2s;
}
.stat-n {
    font-size: 1.45rem;
    font-weight: 800;
    color: #00D1FF;
    line-height: 1;
    display: block;
}
.stat-l {
    font-size: 0.58rem;
    color: #505060;
    margin-top: 3px;
    display: block;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ===== TABS ===== */
[data-testid="stTabs"] > div:first-child {
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid rgba(255, 255, 255, 0.065) !important;
    border-radius: 11px !important;
    padding: 3px !important;
    gap: 2px !important;
    margin-bottom: 12px !important;
}
button[data-baseweb="tab"] {
    background: transparent !important;
    color: #505060 !important;
    border-radius: 8px !important;
    padding: 6px 0 !important;
    font-size: 0.79rem !important;
    font-weight: 500 !important;
    border: none !important;
    transition: all 0.15s !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(0, 255, 157, 0.10) !important;
    color: #00FF9D !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ===== SECTION LABEL ===== */
.sec-label {
    font-size: 0.62rem;
    font-weight: 700;
    color: #3A3A4E;
    text-transform: uppercase;
    letter-spacing: 1.8px;
    flex: 1;
    line-height: 2;
}
.cnt-pill {
    background: rgba(0, 209, 255, 0.08);
    border: 1px solid rgba(0, 209, 255, 0.18);
    border-radius: 20px;
    color: #00D1FF;
    font-size: 0.6rem;
    font-weight: 700;
    padding: 2px 9px;
}

/* ===== ITEM CARDS ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.025) !important;
    border: 1px solid rgba(255, 255, 255, 0.065) !important;
    border-radius: 9px !important;
    padding: 0 5px !important;
    margin-bottom: 3px !important;
    transition: border-color 0.15s !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(255, 255, 255, 0.11) !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0 !important;
}
.item-main {
    font-size: 0.79rem;
    color: #C4C4DC;
    padding: 3px 0 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.item-sub {
    font-size: 0.62rem;
    color: #3C3C52;
    padding-bottom: 3px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ===== DELETE BUTTONS (inside cards, higher specificity) ===== */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stButton"] > button {
    background: rgba(255, 55, 55, 0.07) !important;
    border: 1px solid rgba(255, 55, 55, 0.16) !important;
    color: #FF5555 !important;
    border-radius: 7px !important;
    padding: 3px 9px !important;
    font-size: 0.73rem !important;
    min-height: 0 !important;
    line-height: 1.4 !important;
    height: auto !important;
    width: auto !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stButton"] > button:hover {
    background: rgba(255, 55, 55, 0.14) !important;
    border-color: rgba(255, 55, 55, 0.28) !important;
}

/* ===== ADD POPOVER TRIGGER ===== */
[data-testid="stPopover"] > button {
    background: rgba(0, 255, 157, 0.06) !important;
    border: 1px solid rgba(0, 255, 157, 0.2) !important;
    color: #00FF9D !important;
    border-radius: 20px !important;
    padding: 3px 13px !important;
    font-size: 0.74rem !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
}

/* ===== INPUTS ===== */
[data-testid="stTextInput"] input,
[data-testid="stPasswordInput"] input,
[data-testid="stSelectbox"] > div > div {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 10px !important;
    color: #E0E0F0 !important;
    font-size: 0.84rem !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stPasswordInput"] input::placeholder {
    color: #383848 !important;
}
label[data-testid="stWidgetLabel"] > div > p,
label { font-size: 0.7rem !important; color: #555 !important; }

/* ===== PRIMARY BUTTONS ===== */
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #00FF9D 0%, #00D1FF 100%) !important;
    color: #07070F !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
}

/* ===== SECONDARY/ACTION BUTTONS ===== */
[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(255, 255, 255, 0.06) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #9090A8 !important;
    border-radius: 10px !important;
    font-size: 0.8rem !important;
}

/* ===== SETTINGS CARD ===== */
[data-testid="stVerticalBlockBorderWrapper"].settings-card {
    padding: 12px !important;
}

/* ===== ALERTS ===== */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.78rem !important;
}

/* ===== MISC ===== */
div[data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    align-items: center !important;
}
.stSpinner > div { border-top-color: #00FF9D !important; }
</style>
""", unsafe_allow_html=True)


# ── Session State ─────────────────────────────────────────────────────────────
if "config" not in st.session_state:
    with st.spinner("동기화 중..."):
        st.session_state.config = load_config()

conf = st.session_state.config
recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
sites = conf.get("TARGET_SITES", [])
has_key = bool(conf.get("GEMINI_API_KEY", "").strip())


# ── App Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <span class="app-logo">⚡</span>
    <span class="app-name">Battery Admin</span>
    <span class="app-ver">v2.6</span>
</div>
<div class="stats-row">
    <div class="stat-box">
        <span class="stat-n">{len(recipients)}</span>
        <span class="stat-l">수신인</span>
    </div>
    <div class="stat-box">
        <span class="stat-n">{len(sites)}</span>
        <span class="stat-l">사이트</span>
    </div>
    <div class="stat-box">
        <span class="stat-n" style="font-size:1.1rem; color:{'#00FF9D' if has_key else '#FF5555'}">
            {'✓' if has_key else '✗'}
        </span>
        <span class="stat-l">API 키</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["👥 수신인", "🌐 사이트", "⚙️ 설정"])


# ── Tab 1: Recipients ─────────────────────────────────────────────────────────
with tab1:
    hc, ac = st.columns([5, 2])
    with hc:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:6px">'
            f'<span class="sec-label">수신 목록</span>'
            f'<span class="cnt-pill">{len(recipients)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with ac:
        with st.popover("+ 추가"):
            new_email = st.text_input("이메일 주소", key="new_email", placeholder="name@example.com")
            if st.button("추가하기", key="btn_add_email", type="primary", use_container_width=True):
                if "@" in new_email:
                    recipients.append(new_email.strip())
                    conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
                    st.session_state.config = conf
                    st.success("추가 완료")
                    st.rerun()
                else:
                    st.warning("올바른 이메일 형식이 아닙니다")

    if not recipients:
        st.markdown('<div style="text-align:center;color:#303040;font-size:0.8rem;padding:20px 0">수신인이 없습니다</div>', unsafe_allow_html=True)

    for i, email in enumerate(recipients):
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            c1.markdown(f'<div class="item-main">👤 {email}</div>', unsafe_allow_html=True)
            if c2.button("✕", key=f"del_r{i}"):
                recipients.pop(i)
                conf["EMAIL_RECIPIENT"] = ", ".join(recipients)
                st.session_state.config = conf
                st.rerun()


# ── Tab 2: Sites ──────────────────────────────────────────────────────────────
with tab2:
    hc2, ac2 = st.columns([5, 2])
    with hc2:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:6px">'
            f'<span class="sec-label">수집 사이트</span>'
            f'<span class="cnt-pill">{len(sites)}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with ac2:
        with st.popover("+ 추가"):
            with st.form("add_site"):
                s_name = st.text_input("사이트명", placeholder="Electrive")
                s_url = st.text_input("URL", placeholder="https://...")
                s_cat = st.selectbox(
                    "분류",
                    ["업계 미디어", "설비업체", "대한민국 미디어", "리서치", "중국 동향", "기타"],
                )
                if st.form_submit_button("등록하기", use_container_width=True):
                    if s_name and s_url:
                        sites.append({"name": s_name, "url": s_url, "category": s_cat})
                        conf["TARGET_SITES"] = sites
                        st.session_state.config = conf
                        st.success("등록 완료")
                        st.rerun()
                    else:
                        st.warning("이름과 URL을 입력하세요")

    if not sites:
        st.markdown('<div style="text-align:center;color:#303040;font-size:0.8rem;padding:20px 0">등록된 사이트가 없습니다</div>', unsafe_allow_html=True)

    for i, site in enumerate(sites):
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            url_preview = (site["url"][:26] + "…") if len(site["url"]) > 26 else site["url"]
            with c1:
                st.markdown(
                    f'<div class="item-main">🌐 {site["name"]}</div>'
                    f'<div class="item-sub">{site.get("category", "")} · {url_preview}</div>',
                    unsafe_allow_html=True,
                )
            if c2.button("✕", key=f"del_s{i}"):
                sites.pop(i)
                conf["TARGET_SITES"] = sites
                st.session_state.config = conf
                st.rerun()


# ── Tab 3: Settings ───────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="sec-label" style="margin-bottom:8px">API 설정</div>', unsafe_allow_html=True)

    with st.container(border=True):
        gemini_key = st.text_input(
            "Gemini API Key",
            value=conf.get("GEMINI_API_KEY", ""),
            type="password",
            placeholder="AI 분석에 사용할 Gemini API 키",
        )
        conf["GEMINI_API_KEY"] = gemini_key

    st.markdown('<div class="sec-label" style="margin:14px 0 8px">액션</div>', unsafe_allow_html=True)

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("▶ 실행", key="btn_run", type="primary", use_container_width=True):
            g, rn = get_github_client()
            if g:
                try:
                    g.get_repo(rn).get_workflow("weekly_report.yml").create_dispatch("main")
                    st.success("워크플로 실행 시작")
                except Exception:
                    st.error("실행 실패")
    with b2:
        if st.button("💾 저장", key="btn_save", type="primary", use_container_width=True):
            with st.spinner("저장 중..."):
                if save_config(conf):
                    st.success("저장 완료")
                else:
                    st.error("저장 실패")
    with b3:
        if st.button("🔄 동기화", key="btn_sync", use_container_width=True):
            if "config" in st.session_state:
                del st.session_state["config"]
            st.rerun()
