import streamlit as st
import json
import os
from github import Github
from datetime import datetime, time, timedelta

# Page config
st.set_page_config(page_title="Battery Admin", page_icon="⚡", layout="centered")

# --- CSS: Layout Stabilization ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"], .main { 
        max-width: 100vw !important;
        overflow-x: hidden !important;
        width: 100%;
    }
    .main .block-container { padding: 1rem 0.5rem !important; }
    .header-container { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
    .custom-header { font-size: 1.1rem; font-weight: 800; white-space: nowrap; }
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_"]) {
        display: flex !important; flex-wrap: nowrap !important; gap: 2px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(button[key*="btn_"]) button { font-size: 0.7rem !important; }
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

def update_workflow_schedule(new_time_kst):
    """KST 시간을 UTC cron으로 변환하여 workflow yml 업데이트"""
    g, rn = get_github()
    if not g: return False
    try:
        # KST(UTC+9) -> UTC 변환
        utc_hour = (new_time_kst.hour - 9) % 24
        new_cron = f"{new_time_kst.minute} {utc_hour} * * 0" # 매주 일요일(UTC) -> 월요일(KST) 발송
        
        repo = g.get_repo(rn)
        yml_path = ".github/workflows/weekly_report.yml"
        contents = repo.get_contents(yml_path)
        lines = contents.decoded_content.decode("utf-8").split("\n")
        
        new_lines = []
        for line in lines:
            if "cron:" in line:
                indent = line.split("- cron:")[0]
                new_lines.append(f'{indent}- cron: \'{new_cron}\'  # KST {new_time_kst.strftime("%H:%M")} (Auto-updated)')
            else:
                new_lines.append(line)
        
        repo.update_file(yml_path, f"Update schedule to {new_time_kst}", "\n".join(new_lines), contents.sha)
        return True
    except Exception as e:
        st.error(f"Workflow 업데이트 실패: {e}")
        return False

def save_config(cfg, new_time=None):
    g, rn = get_github()
    if not g: return False
    try:
        repo = g.get_repo(rn)
        # 1. config.json 저장
        c = repo.get_contents("config.json")
        repo.update_file(c.path, "Update config", json.dumps(cfg, indent=2, ensure_ascii=False), c.sha)
        
        # 2. 발송 시간 변경 시 workflow 업데이트
        if new_time:
            update_workflow_schedule(new_time)
        return True
    except: return False

def get_file_content(filename):
    g, rn = get_github()
    if not g: return "GitHub 연동 오류"
    try:
        repo = g.get_repo(rn)
        return repo.get_contents(filename).decoded_content.decode("utf-8")
    except: return "파일이 없습니다."

# --- State ---
if "config" not in st.session_state:
    st.session_state.config = load_config()
if "current_report" not in st.session_state:
    st.session_state.current_report = ""

conf = st.session_state.config

# --- App Content ---
st.title("⚡ Battery Admin")
st.caption("모바일 관리 센터")

tab1, tab2, tab3, tab4 = st.tabs(["👥 수신인", "🌐 사이트", "⚙️ 설정", "📝 리포트"])

with tab1:
    st.markdown('<div class="header-container"><div class="custom-header">수신인</div>', unsafe_allow_html=True)
    with st.popover("➕"):
        email = st.text_input("이메일")
        if st.button("추가", key="add_email", type="primary", use_container_width=True):
            if "@" in email:
                rl = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
                rl.append(email.strip()); conf["EMAIL_RECIPIENT"] = ", ".join(rl)
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    for i, r in enumerate(recipients):
        with st.expander(f"👤 {r}"):
            if st.button("❌ 삭제", key=f"del_r_{i}", type="primary", use_container_width=True):
                recipients.pop(i); conf["EMAIL_RECIPIENT"] = ", ".join(recipients); st.rerun()

with tab2:
    st.markdown('<div class="header-container"><div class="custom-header">사이트</div>', unsafe_allow_html=True)
    with st.popover("➕"):
        with st.form("add_site"):
            n, u = st.text_input("이름"), st.text_input("URL")
            cat = st.selectbox("분류", ["업계 미디어", "설비업체", "기타"])
            if st.form_submit_button("등록", use_container_width=True):
                sl = conf.get("TARGET_SITES", []); sl.append({"name": n, "url": u, "category": cat})
                conf["TARGET_SITES"] = sl; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    sites = conf.get("TARGET_SITES", [])
    for i, s in enumerate(sites):
        with st.expander(f"🌐 {s['name']}"):
            st.caption(s['url'])
            if st.button("❌ 삭제", key=f"del_s_{i}", type="primary", use_container_width=True):
                sites.pop(i); conf["TARGET_SITES"] = sites; st.rerun()

with tab3:
    st.subheader("시스템 설정")
    key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
    conf["GEMINI_API_KEY"] = key
    
    # 정기 발송 시간 설정 추가
    st.markdown("---")
    st.markdown("📅 **정기 리포트 발송 설정**")
    current_time_str = conf.get("SCHEDULE_TIME", "07:00")
    h, m = map(int, current_time_str.split(":"))
    new_time = st.time_input("매주 월요일 발송 시간 (KST)", value=time(h, m))
    conf["SCHEDULE_TIME"] = new_time.strftime("%H:%M")
    st.caption("※ 시간 저장 시 GitHub 발송 스케줄이 즉시 변경됩니다.")

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
            if save_config(conf, new_time): st.success("저장&스케줄 변경 완료!")
    with sc3:
        if st.button("동기", key="btn_sync", use_container_width=True):
            del st.session_state.config; st.rerun()

with tab4:
    st.subheader("📝 최근 발신 리포트")
    report_type = st.radio("종류 선택", ["주간 분석 요약", "트렌드 리포트"], horizontal=True)
    target_file = "weekly_diff_report.md" if report_type == "주간 분석 요약" else "trend_report.md"
    if st.button("리포트 불러오기"):
        with st.spinner("가져오는 중..."): st.session_state.current_report = get_file_content(target_file)
    if st.session_state.current_report:
        st.markdown("---")
        st.markdown(st.session_state.current_report)

st.sidebar.caption("Ver 4.0 (Schedule Sync Added)")
st.sidebar.write(f"수신인: {len(recipients)}명")
st.sidebar.write(f"사이트: {len(sites)}개")
st.sidebar.write(f"발송 시간: 월요일 {conf.get('SCHEDULE_TIME', '07:00')} (KST)")
