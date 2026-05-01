"""
Orchestrator Module
Manages the full workflow: Collect -> Diff -> Analyze -> Report -> Email
Supports two modes:
  - Cloud mode (GitHub Actions): collect + Gemini AI analysis + PPT + email
  - Local mode: collect + NotebookLM upload + AI report + email
"""
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Fix for Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import local modules
from collector import TrendCollector
from weekly_diff import WeeklyDiffTracker
from settings import NOTEBOOK_ID, NOTEBOOK_NAME


def is_cloud_env():
    """Detect if running in GitHub Actions or similar CI."""
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"


def run_cloud_mode():
    """
    Cloud mode: Gemini API for AI analysis (no browser needed).
    Collect data -> Diff -> AI analysis -> PPT -> email.
    """
    print("\n[Mode] ☁️  Cloud mode (Gemini API)")

    # 1. Collect from 10 target sites
    print("\n[Step 1/5] 10개 사이트에서 데이터 수집...")
    collector = TrendCollector()
    collector.collect_from_sites(max_per_site=10)

    total = len(collector.results)
    print(f"[Collector] 총 {total}건 수집 완료.")

    if total == 0:
        print("[Collector] 수집된 데이터가 없습니다. 중단합니다.")
        sys.exit(1)

    report_content = collector.get_combined_report()

    # Save raw report
    with open("trend_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. Weekly diff tracking
    print("\n[Step 2/5] 전주 대비 변화 분석...")
    diff_tracker = WeeklyDiffTracker()
    diff_report, has_new_articles = diff_tracker.generate_diff_report(collector.results)
    print(diff_report[:500])

    # Save diff report
    with open("weekly_diff_report.md", "w", encoding="utf-8") as f:
        f.write(diff_report)

    # 3. AI Analysis via Gemini (with diff context)
    print("\n[Step 3/5] Gemini AI 분석...")
    from ai_analyzer import AIAnalyzer

    # Combine report + diff for richer analysis
    combined_context = f"{report_content}\n\n{diff_report}"

    try:
        analyzer = AIAnalyzer()

        # Deep analysis
        analysis = analyzer.analyze_trends(combined_context)
        if analysis:
            with open("ai_analysis.md", "w", encoding="utf-8") as f:
                f.write(analysis)
            print("[AI] 심층 분석 보고서 저장 완료 (ai_analysis.md)")

        # Slide content
        slides_data = analyzer.generate_slide_content(combined_context)

        # Email body
        email_body = analyzer.generate_email_body(combined_context, analysis)
        if email_body:
            with open("email_preview.md", "w", encoding="utf-8") as f:
                f.write(email_body)
            print("[AI] 이메일 본문 미리보기 저장 완료 (email_preview.md)")

    except Exception as e:
        print(f"[AI] Gemini API 오류: {e}")
        print("[AI] AI 분석 없이 기본 모드로 진행합니다...")
        slides_data = _build_basic_slides(collector)
        email_body = _build_basic_email(collector)
        analysis = None

    # 4. PPT Generation
    print("\n[Step 4/5] PPT 생성 (Premium Design)...")
    from ppt_generator import PPTGenerator

    if not slides_data:
        print("[PPT] AI 슬라이드 데이터 없음. 기본 슬라이드로 대체합니다.")
        slides_data = _build_basic_slides(collector)

    # Attempt to generate a background image for the title slide
    bg_image_path = None
    try:
        print("[PPT] 제목 슬라이드용 AI 배경 이미지 생성 중...")
        # Note: We use a simplified prompt for the orchestrator to call
        # In a real scenario, this would call the generate_image tool or an API
        # Since I am an agent, I will assume the image path from my previous generation
        # or skip if not in a context where I can call tools during runtime easily.
        # However, for this task, I'll provide the path I just generated.
        bg_image_path = os.path.join(os.getcwd(), "battery_future_tech_bg.png")
        
        # If the file doesn't exist (e.g. first run), we can provide a default or skip
        if not os.path.exists(bg_image_path):
            print("[PPT] AI 이미지를 찾을 수 없어 기본 배경으로 진행합니다.")
            bg_image_path = None
    except Exception as e:
        print(f"[PPT] 이미지 생성/로드 실패: {e}")

    ppt_gen = PPTGenerator()
    ppt_file = ppt_gen.create_presentation(slides_data, "battery_trend_report.pptx", bg_image_path=bg_image_path)
    print(f"[PPT] 저장 완료: {ppt_file}")

    # 5. Email
    print("\n[Step 5/5] 이메일 발송...")
    from mailer import EmailSender
    from settings import EMAIL_RECIPIENT

    if not email_body:
        email_body = _build_basic_email(collector)

    if EMAIL_RECIPIENT:
        mailer = EmailSender()
        today = datetime.now().strftime("%Y-%m-%d")
        subject = f"[Weekly] 2차전지 업계 동향 리포트 ({today})"

        attachments = [ppt_file]
        # Also attach analysis markdown if exists
        analysis_path = os.path.join(os.getcwd(), "ai_analysis.md")
        if os.path.exists(analysis_path):
            attachments.append(analysis_path)

        if mailer.send_email(EMAIL_RECIPIENT, subject, email_body, attachment_path=ppt_file):
            print("[Mailer] ✅ 이메일 발송 성공!")
        else:
            print("[Mailer] ❌ 이메일 발송 실패.")
            sys.exit(1)
    else:
        print("[Mailer] 수신자가 설정되지 않았습니다.")
        sys.exit(1)


def _build_basic_slides(collector):
    """Fallback: build basic slides from raw collected data."""
    from settings import TARGET_SITES
    slides_data = []

    # Group by category
    categories = {}
    for r in collector.results:
        cat = r.get("category", "기타")
        categories.setdefault(cat, []).append(r)

    for cat, items in categories.items():
        slide = {'title': f'{cat} — 주요 헤드라인', 'content': []}
        for r in items[:6]:
            slide['content'].append(f"[{r.get('site', '')}] {r.get('title', 'N/A')}")
            slide['content'].append(f"  🔗 {r.get('url', '')}")
        slides_data.append(slide)

    return slides_data


def _build_basic_email(collector):
    """Fallback: build basic email from raw collected data."""
    today = datetime.now().strftime("%Y-%m-%d")
    body = f"안녕하세요,\n\n금주({today})의 2차전지/배터리 업계 동향 리포트를 발송합니다.\n\n"
    body += "=" * 50 + "\n📰 10개 전문 사이트 주요 헤드라인\n" + "=" * 50 + "\n\n"
    for i, item in enumerate(collector.results[:15], 1):
        body += f"{i}. [{item.get('site', '')}] {item.get('title', 'N/A')}\n"
        body += f"   🔗 {item.get('url', '')}\n\n"
    body += "상세 내용은 첨부된 PPT를 참조 부탁드립니다.\n감사합니다.\n"
    return body


def run_local_mode(args):
    """
    Local mode: Uses NotebookLM for AI-powered report generation.
    """
    print("\n[Mode] 🖥️  Local mode (NotebookLM)")

    from auth_manager import AuthManager

    # 1. Authentication Check
    auth = AuthManager()
    if args.force_auth or not auth.is_authenticated():
        print("\n[Auth] 인증이 필요합니다.")
        if auth.setup_auth(headless=False):
            print("[Auth] 인증 성공!")
        else:
            print("[Auth] 인증 실패.")
            return

    # 2. Data Collection from 10 target sites
    print("\n[Collector] 10개 사이트에서 데이터 수집 중...")
    collector = TrendCollector()
    collector.collect_from_sites(max_per_site=10)

    total = len(collector.results)
    print(f"[Collector] 총 {total}건 수집 완료.")

    # 3. Weekly diff tracking
    print("\n[Diff] 전주 대비 변화 분석 중...")
    diff_tracker = WeeklyDiffTracker()
    diff_report, has_new_articles = diff_tracker.generate_diff_report(collector.results)
    print(diff_report[:500])

    with open("weekly_diff_report.md", "w", encoding="utf-8") as f:
        f.write(diff_report)

    report_content = collector.get_combined_report()

    if args.collect_only:
        print("\nReport Content Preview:")
        print(report_content[:500] + "...")
        print("\n--- Weekly Diff ---")
        print(diff_report)
        return

    # 4. Upload to NotebookLM
    notebook_url = None
    if NOTEBOOK_ID:
        notebook_url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"

    if notebook_url:
        print("\n[Uploader] NotebookLM에 업로드 중...")
        from uploader import NotebookUploader
        uploader = NotebookUploader(notebook_url)
        try:
            # Include diff report in the upload
            upload_content = f"{report_content}\n\n{diff_report}"
            uploader.upload_text("Trend Report", upload_content)
            print("[Uploader] 업로드 성공!")
        except Exception as e:
            print(f"[Uploader] 업로드 실패: {e}")
            print("[Uploader] 기존 소스로 계속 진행합니다...")

    # 5. Generate Report via NotebookLM
    if notebook_url:
        print("\n[Reporter] 매거진 리포트 생성 중...")
        from reporter import NotebookReporter
        reporter = NotebookReporter(notebook_url)

        prompt = (
            "새로 추가된 자료를 바탕으로 2차전지 제조공정·설비 업계의 최근 이슈 4가지를 선정하여 심층 분석 리포트를 작성해줘. "
            "반드시 다음 4가지를 집중적으로 파악해서 반영해줘: "
            "1) 배터리 제조공정 제조사별 비교 분석, "
            "2) 신규 제조 설비 및 새로운 공법 동향, "
            "3) 국내/중국 설비업체 동향 집중 조명, "
            "4) 배터리 관련 전시회 전시 항목과 신기술 트렌드. "
            "각 이슈에 대해 '현황', '주요 원인(배경)', '신규 공법/설비 파급효과', '미래 전망'을 포함하여 자세히 서술할 것. "
            "매거진 특집 기사 스타일로 서론과 에디터 노트도 포함해."
        )
        report_text = reporter.generate_report(prompt)

        if report_text:
            with open("trend_report.md", "w", encoding="utf-8") as f:
                f.write(report_text)

            # PPT via Studio slides
            print("\n[Reporter] Studio Slides 새로 생성 및 다운로드 중...")
            ppt_file = os.path.join(os.getcwd(), "battery_trend_report_ai.pptx")
            try:
                uploader.download_studio_slides(ppt_file, force_new=True)
                print(f"[PPT] 스튜디오에서 새롭게 생성된 PPT 저장 완료: {ppt_file}")
            except Exception as e:
                print(f"[PPT] Studio Slides 생성 실패: {e}, 로컬로 대체합니다...")
                slide_prompt = (
                    "앞서 작성한 4가지 이슈를 바탕으로 PPT 슬라이드 내용을 작성해줘. "
                    "각 이슈마다 슬라이드 1개씩 할당. "
                    "내용 작성 시 반드시 다음 항목들을 위주로 요구해줘: "
                    "배터리 제조공정 제조사별 비교 분석, 신규 제조 설비 및 새로운 공법 동향, 국내/중국 설비업체 동향 집중 조명, 배터리 관련 전시회 전시 항목과 신기술 트렌드. "
                    "형식:\nTitle: [이슈 제목]\n- [상세 설명 1]\n- [상세 설명 2]..."
                )
                slides_data = reporter.generate_slide_content(slide_prompt)
                if slides_data:
                    from ppt_generator import PPTGenerator
                    ppt_gen = PPTGenerator()
                    ppt_file = ppt_gen.create_presentation(slides_data, "battery_trend_report_local.pptx")
                    print(f"[PPT] 로컬 PPT 저장 완료: {ppt_file}")

            # Email
            print("\n[Reporter] 이메일 본문 생성 중...")
            summary_prompt = (
                "앞서 작성한 리포트 내용을 바탕으로 이메일 본문을 작성해줘. "
                "정중한 인사말을 시작으로 핵심 이슈 전부를 요약 (관련 원본 소스 링크 URL 포함) 정리하고, "
                "전주 대비 새로운 소식도 추가하고 맺음말로 결론지을 것."
            )
            email_body = reporter.generate_email_summary(summary_prompt) or "리포트가 첨부되었습니다."

            print("\n[Mailer] 이메일 발송 중...")
            from mailer import EmailSender
            from settings import EMAIL_RECIPIENT

            if EMAIL_RECIPIENT:
                mailer = EmailSender()
                subject = "Battery Trend Report (Weekly)"
                if mailer.send_email(EMAIL_RECIPIENT, subject, email_body, attachment_path=ppt_file):
                    print("[Mailer] ✅ 이메일 발송 성공!")
                else:
                    print("[Mailer] ❌ 이메일 발송 실패.")
            else:
                print("[Mailer] 수신자 미설정.")
        else:
            print("[Reporter] 리포트 생성 실패.")


def main():
    parser = argparse.ArgumentParser(description='Battery Trend Reporter')
    parser.add_argument('--collect-only', action='store_true', help='Only collect data and show diff')
    parser.add_argument('--force-auth', action='store_true', help='Force re-auth')
    parser.add_argument('--cloud', action='store_true', help='Force cloud mode (Gemini API)')
    args = parser.parse_args()

    print("=== ⚡ Battery Trend Reporter ===")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📡 10개 전문 사이트 직접 수집 모드")

    if args.cloud or is_cloud_env():
        run_cloud_mode()
    else:
        run_local_mode(args)

    print("\n=== ✅ Workflow Complete ===")


if __name__ == "__main__":
    main()
