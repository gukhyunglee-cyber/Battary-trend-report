import streamlit as st
import streamlit.components.v1 as components
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
    padding: 0.4rem 0.75rem 1rem !important;
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
    padding: 6px 0 8px;
    border-bottom: 1px solid rgba(0,255,157,0.12);
    margin-bottom: 8px;
    gap: 6px;
}
.app-logo { font-size: 1.1rem; }
.app-name {
    font-size: 1rem;
    font-weight: 800;
    background: linear-gradient(90deg, #00FF9D 0%, #00D1FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    flex: 1;
}
.app-ver {
    font-size: 0.55rem;
    color: rgba(0,255,157,0.4);
    border: 1px solid rgba(0,255,157,0.15);
    border-radius: 20px;
    padding: 1px 7px;
}

/* ===== STATS ===== */
.stats-row { display: flex; gap: 5px; margin-bottom: 8px; }
.stat-box {
    flex: 1;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 9px;
    padding: 6px 4px 5px;
    text-align: center;
}
.stat-n { font-size: 1.2rem; font-weight: 800; color: #00D1FF; line-height: 1; display: block; }
.stat-l { font-size: 0.55rem; color: #454558; margin-top: 2px; display: block;
          text-transform: uppercase; letter-spacing: 0.5px; }

/* ===== TABS ===== */
[data-testid="stTabs"] > div:first-child {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
    padding: 2px !important;
    gap: 2px !important;
    margin-bottom: 8px !important;
}
button[data-baseweb="tab"] {
    background: transparent !important;
    color: #454558 !important;
    border-radius: 8px !important;
    padding: 5px 0 !important;
    font-size: 0.77rem !important;
    font-weight: 500 !important;
    border: none !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(0,255,157,0.10) !important;
    color: #00FF9D !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ===== SECTION LABEL ===== */
.custom-header {
    font-size: 1.1rem !important;
    font-weight: 800 !important;
    color: #E0E0F0 !important;
    white-space: nowrap !important;
}
.sec-label {
    font-size: 0.58rem;
    font-weight: 700;
    color: #323244;
    text-transform: uppercase;
    letter-spacing: 1.8px;
    flex: 1;
    line-height: 2;
}
.cnt-pill {
    background: rgba(0,209,255,0.07);
    border: 1px solid rgba(0,209,255,0.15);
    border-radius: 20px;
    color: #00D1FF;
    font-size: 0.58rem;
    font-weight: 700;
    padding: 1px 8px;
}

/* ===== ITEM CARDS ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.025) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 9px !important;
    padding: 0 8px !important;
    margin-bottom: 2px !important;
    position: relative !important;
    overflow: hidden !important;
    -webkit-user-select: none !important;
    user-select: none !important;
    -webkit-touch-callout: none !important;
    transition: border-color 0.2s, background 0.2s !important;
    cursor: default !important;
}

/* ===== HOLD PROGRESS BAR ===== */
[data-testid="stVerticalBlockBorderWrapper"]::after {
    content: '' !important;
    position: absolute !important;
    bottom: 0 !important;
    left: 0 !important;
    height: 2px !important;
    width: 0 !important;
    background: linear-gradient(90deg, #FF4444, #FF8888) !important;
    transition: none !important;
    pointer-events: none !important;
    z-index: 10 !important;
    border-radius: 0 0 9px 9px !important;
}
[data-testid="stVerticalBlockBorderWrapper"].holding::after {
    width: 100% !important;
    transition: width 0.6s linear !important;
}
[data-testid="stVerticalBlockBorderWrapper"].holding {
    border-color: rgba(255,100,100,0.2) !important;
}

/* ===== ITEM TEXT ===== */
.item-main {
    font-size: 0.78rem;
    color: #C4C4DC;
    padding: 5px 0 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.item-sub {
    font-size: 0.61rem;
    color: #383850;
    padding-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ===== HIDE per-item delete button (kept clickable via JS) ===== */
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stButton"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stElementContainer"]:has([data-testid="stButton"]) {
    height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stButton"] > button {
    position: absolute !important;
    width: 1px !important;
    height: 1px !important;
    opacity: 0 !important;
    top: 0 !important;
    left: 0 !important;
    pointer-events: none !important;
}

/* ===== ADD POPOVER ===== */
[data-testid="stPopover"] > button {
    background: rgba(0,255,157,0.06) !important;
    border: 1px solid rgba(0,255,157,0.18) !important;
    color: #00FF9D !important;
    border-radius: 20px !important;
    padding: 2px 12px !important;
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    white-space: nowrap !important;
}

/* ===== INPUTS ===== */
[data-testid="stTextInput"] input,
[data-testid="stPasswordInput"] input,
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 9px !important;
    color: #E0E0F0 !important;
    font-size: 0.83rem !important;
}
label[data-testid="stWidgetLabel"] > div > p,
label { font-size: 0.68rem !important; color: #555 !important; }

/* ===== ACTION BUTTONS in settings (NOT inside item cards) ===== */
[data-testid="stButton"] > button[kind="primary"],
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #00FF9D 0%, #00D1FF 100%) !important;
    color: #07070F !important;
    border: none !important;
    border-radius: 9px !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
}
[data-testid="stButton"] > button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #9090A8 !important;
    border-radius: 9px !important;
    font-size: 0.78rem !important;
}

/* ===== SETTINGS CARD (has input) ===== */
[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]),
[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stPasswordInput"]) {
    padding: 8px 10px !important;
    cursor: auto !important;
    -webkit-user-select: auto !important;
    user-select: auto !important;
}

/* ===== ALERTS ===== */
[data-testid="stAlert"] { border-radius: 9px !important; font-size: 0.76rem !important; }

/* ===== MISC ===== */
div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; align-items: center !important; }
[data-testid="stCustomComponentV1"] iframe { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Context Menu + Long Press / Right-click JS ────────────────────────────────
components.html("""
<script>
(function () {
    const p = window.parent.document;
    if (p.getElementById('__bc_menu')) return;

    /* ── Build context menu in parent doc ── */
    const menu = p.createElement('div');
    menu.id = '__bc_menu';
    Object.assign(menu.style, {
        position: 'fixed', display: 'none', zIndex: '999999',
        background: '#12121E', border: '1px solid rgba(255,55,55,0.3)',
        borderRadius: '10px', overflow: 'hidden',
        boxShadow: '0 8px 32px rgba(0,0,0,0.7)', minWidth: '120px',
    });

    const item = p.createElement('div');
    item.id = '__bc_del';
    item.textContent = '🗑  삭제';
    Object.assign(item.style, {
        padding: '10px 18px', fontSize: '0.82rem', fontWeight: '700',
        color: '#FF5555', cursor: 'pointer', userSelect: 'none',
        fontFamily: '-apple-system, sans-serif',
    });
    item.addEventListener('mouseover', () => item.style.background = 'rgba(255,55,55,0.1)');
    item.addEventListener('mouseout',  () => item.style.background = 'transparent');
    menu.appendChild(item);
    p.body.appendChild(menu);

    let pendingWrap = null;

    function showMenu(x, y, wrap) {
        pendingWrap = wrap;
        menu.style.display = 'block';
        const vw = p.documentElement.clientWidth;
        const vh = p.documentElement.clientHeight;
        menu.style.left = Math.min(x, vw - 140) + 'px';
        menu.style.top  = Math.min(y, vh - 52)  + 'px';
        console.log('[battery] menu shown for', wrap);
    }

    function hideMenu() {
        menu.style.display = 'none';
        pendingWrap = null;
    }

    /* ── On 삭제 click: find hidden Streamlit button inside the card and click it ── */
    item.addEventListener('click', () => {
        if (!pendingWrap) {
            console.warn('[battery] no pending wrap');
            return;
        }
        const btn = pendingWrap.querySelector('[data-testid="stButton"] button')
                 || pendingWrap.querySelector('button');
        if (!btn) {
            console.error('[battery] hidden button not found in card');
            hideMenu();
            return;
        }
        item.textContent = '⏳  삭제 중...';
        item.style.color = '#888';
        btn.click();
        console.log('[battery] clicked', btn);
        setTimeout(() => {
            item.textContent = '🗑  삭제';
            item.style.color = '#FF5555';
            hideMenu();
        }, 300);
    });

    /* ── Dismiss on outside click/touch ── */
    p.addEventListener('mousedown',  e => { if (!menu.contains(e.target)) hideMenu(); });
    p.addEventListener('touchstart', e => { if (!menu.contains(e.target)) hideMenu(); }, { passive: true });
    p.addEventListener('scroll',     hideMenu, { passive: true });

    /* ── Mark a wrap as deletable only if it has hidden button + .item-main ── */
    function isDeletable(wrap) {
        return !!(wrap.querySelector('.item-main') && wrap.querySelector('button'));
    }

    /* ── Attach long-press / right-click handlers ── */
    function setup() {
        p.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]').forEach(w => {
            if (w.dataset.bcSetup) return;
            if (!isDeletable(w)) return;
            w.dataset.bcSetup = '1';

            let timer = null;

            /* Mobile: long press */
            w.addEventListener('touchstart', e => {
                const t = e.touches[0];
                w.classList.add('holding');
                timer = setTimeout(() => {
                    w.classList.remove('holding');
                    if (navigator.vibrate) navigator.vibrate(40);
                    showMenu(t.clientX, t.clientY, w);
                }, 600);
            }, { passive: true });
            w.addEventListener('touchend',   () => { clearTimeout(timer); w.classList.remove('holding'); });
            w.addEventListener('touchmove',  () => { clearTimeout(timer); w.classList.remove('holding'); });

            /* PC: right-click */
            w.addEventListener('contextmenu', e => {
                e.preventDefault();
                showMenu(e.clientX, e.clientY, w);
            });

            /* PC: visual hold feedback */
            w.addEventListener('mousedown', e => {
                if (e.button !== 0) return;
                w.classList.add('holding');
                timer = setTimeout(() => w.classList.remove('holding'), 600);
            });
            w.addEventListener('mouseup',    () => { clearTimeout(timer); w.classList.remove('holding'); });
            w.addEventListener('mouseleave', () => { clearTimeout(timer); w.classList.remove('holding'); });
        });
        console.log('[battery] setup done, deletable cards:',
            p.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"][data-bc-setup="1"]').length);
    }

    new MutationObserver(setup).observe(p.body, { childList: true, subtree: true });
    setup();
    [100, 300, 800, 1500].forEach(t => setTimeout(setup, t));
})();
</script>
""", height=0)

# ── Session State ─────────────────────────────────────────────────────────────
if "config" not in st.session_state:
    with st.spinner("동기화 중..."):
        st.session_state.config = load_config_from_github()
        st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")

conf = st.session_state.config
recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
sites = conf.get("TARGET_SITES", [])
has_key = bool(conf.get("GEMINI_API_KEY", "").strip())
if "delete_confirm" not in st.session_state: st.session_state.delete_confirm = None

# Global Delete Confirmation (Fixed overlay style for mobile)
if st.session_state.delete_confirm:
    type_key, idx, val = st.session_state.delete_confirm
    with st.status("⚠️ 삭제 확인", expanded=True):
        st.write(f"다음 항목을 삭제하시겠습니까?\n\n**{val}**")
        c1, c2 = st.columns(2)
        if c1.button("확인", type="primary", use_container_width=True):
            if type_key == "email":
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
st.sidebar.caption(f"Ver 2.6 (Premium UI)")
st.sidebar.write(f"📧 수신인: {len(recipients)}명")
st.sidebar.write(f"🌐 사이트: {len(sites)}개")
if "last_sync" in st.session_state:
    st.sidebar.caption(f"최근 동기화: {st.session_state.last_sync}")


# ── App Header ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="app-header">
    <span class="app-logo">⚡</span>
    <span class="app-name">Battery Admin</span>
    <span class="app-ver">v2.9</span>
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
        <span class="stat-n" style="font-size:1rem;color:{'#00FF9D' if has_key else '#FF5555'}">
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
    hc, ac, ec = st.columns([2, 2, 6])
    with hc:
        st.markdown(
            f'<div class="custom-header">수신인</div>',
            unsafe_allow_html=True,
        )
    with ac:
        with st.popover("➕"):
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
        st.markdown('<div style="text-align:center;color:#2A2A3C;font-size:0.75rem;padding:14px 0">수신인 없음</div>', unsafe_allow_html=True)

    for i, email in enumerate(recipients):
        with st.container(border=True):
            st.markdown(f'<div class="item-main">👤 {email}</div>', unsafe_allow_html=True)
            if st.button("del", key=f"_del_r_{i}"):
                st.session_state.delete_confirm = ("email", i, email)
                st.rerun()


# ── Tab 2: Sites ──────────────────────────────────────────────────────────────
with tab2:
    hc2, ac2, ec2 = st.columns([2, 2, 6])
    with hc2:
        st.markdown(
            f'<div class="custom-header">사이트</div>',
            unsafe_allow_html=True,
        )
    with ac2:
        with st.popover("➕"):
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
        st.markdown('<div style="text-align:center;color:#2A2A3C;font-size:0.75rem;padding:14px 0">등록된 사이트 없음</div>', unsafe_allow_html=True)

    for i, site in enumerate(sites):
        cat_emoji = {
            "업계 미디어": "📰", "설비업체": "🏗️", "대한민국 미디어": "🇰🇷", 
            "리서치": "📊", "중국 동향": "🇨🇳", "기타": "🔗"
        }.get(site.get('category', '기타'), "🔗")
        
        with st.expander(f"{cat_emoji} {site['name']}"):
            st.write(f"**URL:** {site['url']}")
            st.info(f"분류: {site.get('category', '미지정')}")
            if st.button("❌ 삭제하기", key=f"del_site_{i}", type="primary", use_container_width=True):
                st.session_state.delete_confirm = ("site", i, site['name'])
                st.rerun()


# ── Tab 3: Settings ───────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="sec-label" style="margin-bottom:6px">API 설정</div>', unsafe_allow_html=True)

    with st.container(border=True):
        gemini_key = st.text_input(
            "Gemini API Key",
            value=conf.get("GEMINI_API_KEY", ""),
            type="password",
            placeholder="AI 분석 API 키",
        )
        conf["GEMINI_API_KEY"] = gemini_key

    st.markdown('<div class="sec-label" style="margin:10px 0 6px">액션</div>', unsafe_allow_html=True)
    repo_url = f"https://github.com/{st.secrets.get('GITHUB_REPO', '')}/actions"
    st.link_button("🚀 실행 기록 (GitHub)", repo_url, use_container_width=True)

    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("▶ 실행", key="btn_run", type="primary", use_container_width=True):
            g, rn = get_github_client()
            if g:
                try:
                    g.get_repo(rn).get_workflow("weekly_report.yml").create_dispatch("main")
                    st.success("실행 시작")
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
