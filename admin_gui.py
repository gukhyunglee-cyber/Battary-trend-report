import streamlit as st
import json
import os
import base64
import time
from github import Github
from datetime import datetime, time as dtime, timedelta

# Page config
st.set_page_config(page_title="Battery BM", page_icon="battery_bm_icon.png", layout="centered")

# --- CSS ---
st.markdown("""
<style>
    html, body, [data-testid="stAppViewContainer"], .main { 
        max-width: 100vw !important;
        overflow-x: hidden !important;
        width: 100%;
    }
    .main .block-container { padding: 1rem 0.5rem !important; }
    .header-container { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; margin-top: 10px; }
    .custom-header { font-size: 1.1rem; font-weight: 800; white-space: nowrap; }
    .report-box { background-color: #1E1E2E; padding: 15px; border-radius: 10px; border: 1px solid #3E3E4E; }
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

def get_file_data(filename, is_binary=False):
    g, rn = get_github()
    if not g: return None
    try:
        repo = g.get_repo(rn)
        content = repo.get_contents(filename)
        if is_binary:
            if content.size > 1000000:
                blob = repo.get_git_blob(content.sha)
                return base64.b64decode(blob.content)
            return content.decoded_content
        return content.decoded_content.decode("utf-8")
    except: return None

def monitor_workflow(repo, workflow_name):
    with st.status("🚀 프로세스 시작...", expanded=True) as status:
        workflow = repo.get_workflow(workflow_name)
        workflow.create_dispatch("main")
        time.sleep(5)
        last_run = None
        for _ in range(60):
            runs = workflow.get_runs()
            if runs.totalCount > 0:
                latest = runs[0]
                if latest.status in ["in_progress", "queued", "waiting"]:
                    last_run = latest; break
            time.sleep(2)
        if not last_run: status.update(label="❌ 지연", state="error"); return
        while True:
            last_run.update()
            if last_run.status == "in_progress": status.update(label="⚙️ 생성 중...", state="running")
            elif last_run.status == "completed":
                if last_run.conclusion == "success":
                    status.update(label="✅ 완료!", state="complete")
                    st.toast("완료되었습니다!"); time.sleep(2); st.rerun()
                else: status.update(label="❌ 실패", state="error"); break
            time.sleep(10)

def update_workflow_schedule(new_day_kst, new_time_kst):
    g, rn = get_github()
    if not g: return False
    try:
        days_map = {"월": 1, "화": 2, "수": 3, "목": 4, "금": 5, "토": 6, "일": 0}
        kst_day_num = days_map.get(new_day_kst, 1)
        utc_hour = (new_time_kst.hour - 9) % 24
        day_offset = -1 if new_time_kst.hour < 9 else 0
        utc_day = (kst_day_num + day_offset) % 7
        new_cron = f"{new_time_kst.minute} {utc_hour} * * {utc_day}"
        repo = g.get_repo(rn)
        yml_path = ".github/workflows/weekly_report.yml"
        contents = repo.get_contents(yml_path)
        repo.update_file(yml_path, f"Update schedule", contents.decoded_content.decode("utf-8"), contents.sha)
        return True
    except: return False

def save_config(cfg, new_day, new_time):
    g, rn = get_github()
    if not g: return False
    try:
        repo = g.get_repo(rn)
        c = repo.get_contents("config.json")
        repo.update_file(c.path, "Update config", json.dumps(cfg, indent=2, ensure_ascii=False), c.sha)
        update_workflow_schedule(new_day, new_time)
        return True
    except: return False

# --- State ---
if "config" not in st.session_state: st.session_state.config = load_config()
if "current_report" not in st.session_state: st.session_state.current_report = ""
if "ppt_ai_ready" not in st.session_state: st.session_state.ppt_ai_ready = None
if "ppt_base_ready" not in st.session_state: st.session_state.ppt_base_ready = None
conf = st.session_state.config

# --- UI ---
st.title("⚡ Battery BM")
tab1, tab2, tab3, tab4 = st.tabs(["👥 수신인", "🌐 사이트", "⚙️ 설정", "📝 리포트"])

with tab1:
    st.markdown('<div class="header-container"><div class="custom-header">수신인 관리</div>', unsafe_allow_html=True)
    with st.popover("➕"):
        email = st.text_input("이메일")
        if st.button("추가", key="add_email", type="primary", use_container_width=True):
            if "@" in email:
                rl = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
                rl.append(email.strip()); conf["EMAIL_RECIPIENT"] = ", ".join(rl); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    recipients = [r.strip() for r in conf.get("EMAIL_RECIPIENT", "").split(",") if r.strip()]
    for i, r in enumerate(recipients):
        with st.expander(f"👤 {r}"):
            if st.button("❌ 삭제", key=f"del_r_{i}", type="primary", use_container_width=True):
                recipients.pop(i); conf["EMAIL_RECIPIENT"] = ", ".join(recipients); st.rerun()

with tab2:
    st.markdown('<div class="header-container"><div class="custom-header">사이트 모니터링</div>', unsafe_allow_html=True)
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
    st.markdown('<div class="header-container"><div class="custom-header">시스템 설정</div></div>', unsafe_allow_html=True)
    key = st.text_input("Gemini API Key", value=conf.get("GEMINI_API_KEY", ""), type="password")
    conf["GEMINI_API_KEY"] = key
    st.markdown("---")
    st.markdown("📅 **정기 리포트 발송 설정**")
    days_list = ["월", "화", "수", "목", "금", "토", "일"]
    new_day = st.selectbox("발송 요일 (KST)", options=days_list, index=days_list.index(conf.get("SCHEDULE_DAY", "월")))
    conf["SCHEDULE_DAY"] = new_day
    h, m = map(int, conf.get("SCHEDULE_TIME", "07:00").split(":"))
    new_time = st.time_input("발송 시간 (KST)", value=dtime(h, m))
    conf["SCHEDULE_TIME"] = new_time.strftime("%H:%M")
    
    st.markdown("### 🚀 액션")
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        if st.button("실행", key="btn_run", use_container_width=True, type="primary"):
            g, rn = get_github()
            if g: monitor_workflow(g.get_repo(rn), "weekly_report.yml")
    with sc2:
        if st.button("저장", key="btn_save", use_container_width=True):
            if save_config(conf, new_day, new_time): st.success("OK")
    with sc3:
        if st.button("동기", key="btn_sync", use_container_width=True): del st.session_state.config; st.rerun()

with tab4:
    st.markdown('<div class="header-container"><div class="custom-header">리포트 센터</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="header-container"><div class="custom-header">📊 PPT 리포트 다운로드</div></div>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        if st.button("🔍 AI PPT 찾기", use_container_width=True):
            with st.spinner("로딩..."): st.session_state.ppt_ai_ready = get_file_data("battery_trend_report_ai.pptx", is_binary=True)
        if st.session_state.ppt_ai_ready:
            st.download_button("💾 AI PPT 저장", st.session_state.ppt_ai_ready, "battery_trend_report_ai.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)
    with p2:
        if st.button("🔍 기본 PPT 찾기", use_container_width=True):
            with st.spinner("로딩..."): st.session_state.ppt_base_ready = get_file_data("battery_trend_report.pptx", is_binary=True)
        if st.session_state.ppt_base_ready:
            st.download_button("💾 기본 PPT 저장", st.session_state.ppt_base_ready, "battery_trend_report.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", use_container_width=True)

    st.markdown("---")
    st.markdown('<div class="header-container"><div class="custom-header">👁️ 내용 미리보기</div></div>', unsafe_allow_html=True)
    r_type = st.radio("종류", ["주간 분석 요약", "트렌드 리포트 (PPT 내용)", "📧 이메일 본문"], horizontal=True)
    if st.button("내용 불러오기", type="primary", use_container_width=True):
        if r_type == "주간 분석 요약": f = "weekly_diff_report.md"
        elif r_type == "📧 이메일 본문": f = "email_preview.md"
        else: f = "trend_report.md"
        st.session_state.current_report = get_file_data(f)
    if st.session_state.current_report:
        st.markdown('<div class="report-box">', unsafe_allow_html=True); st.markdown(st.session_state.current_report); st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.image("battery_bm_icon.png", width=100)
st.sidebar.title("Battery BM")
st.sidebar.caption("Ver 5.2 (Hierarchy Unified)")
