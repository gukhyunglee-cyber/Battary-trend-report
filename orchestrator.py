"""
Orchestrator Module
Manages the full workflow: Collect -> Analyze -> Report -> Email
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
from settings import NOTEBOOK_ID, NOTEBOOK_NAME


def is_cloud_env():
    """Detect if running in GitHub Actions or similar CI."""
    return os.getenv("CI") == "true" or os.getenv("GITHUB_ACTIONS") == "true"


def run_cloud_mode():
    """
    Cloud mode: Gemini API for AI analysis (no browser needed).
    Collect data -> AI analysis -> PPT -> email.
    """
    print("\n[Mode] ☁️  Cloud mode (Gemini API)")

    # 1. Collect
    print("\n[Step 1/4] 데이터 수집...")
    collector = TrendCollector()
    print("  - 웹 검색 중...")
    collector.collect_web_trends(5)
    print("  - YouTube 검색 중...")
    collector.collect_youtube_trends(3)

    report_content = collector.get_combined_report()
    total = len(collector.web_results) + len(collector.youtube_results)
    print(f"[Collector] 총 {total}건 수집 완료.")

    if total == 0:
        print("[Collector] 수집된 데이터가 없습니다. 중단합니다.")
        sys.exit(1)

    # Save raw report
    with open("trend_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. AI Analysis via Gemini
    print("\n[Step 2/4] Gemini AI 분석...")
    from ai_analyzer import AIAnalyzer

    try:
        analyzer = AIAnalyzer()

        # Deep analysis
        analysis = analyzer.analyze_trends(report_content)
        if analysis:
            with open("ai_analysis.md", "w", encoding="utf-8") as f:
                f.write(analysis)
            print("[AI] 심층 분석 보고서 저장 완료 (ai_analysis.md)")

        # Slide content
        slides_data = analyzer.generate_slide_content(report_content)

        # Email body
        email_body = analyzer.generate_email_body(report_content, analysis)

    except Exception as e:
        print(f"[AI] Gemini API 오류: {e}")
        print("[AI] AI 분석 없이 기본 모드로 진행합니다...")
        slides_data = _build_basic_slides(collector)
        email_body = _build_basic_email(collector)
        analysis = None

    # 3. PPT Generation
    print("\n[Step 3/4] PPT 생성...")
    from ppt_generator import PPTGenerator

    if not slides_data:
        print("[PPT] AI 슬라이드 데이터 없음. 기본 슬라이드로 대체합니다.")
        slides_data = _build_basic_slides(collector)

    ppt_gen = PPTGenerator()
    ppt_file = ppt_gen.create_presentation(slides_data, "battery_trend_report.pptx")
    print(f"[PPT] 저장 완료: {ppt_file}")

    # 4. Email
    print("\n[Step 4/4] 이메일 발송...")
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
    from settings import SEARCH_KEYWORDS_KR
    slides_data = []

    for kw in SEARCH_KEYWORDS_KR:
        matching = [r for r in collector.web_results
                    if any(w in (r.get('title', '') + r.get('description', ''))
                           for w in kw.split())]
        if not matching:
            continue
        slide = {'title': kw, 'content': []}
        for r in matching[:4]:
            slide['content'].append(r.get('title', 'N/A'))
            slide['content'].append(f"  {r.get('description', '')[:120]}")
            slide['content'].append(f"  🔗 {r.get('url', '')}")
        slides_data.append(slide)

    if collector.youtube_results:
        yt_slide = {'title': 'YouTube - 배터리 관련 최신 영상', 'content': []}
        for v in collector.youtube_results[:5]:
            yt_slide['content'].append(v.get('title', 'N/A'))
            yt_slide['content'].append(f"  🔗 {v.get('url', '')}")
        slides_data.append(yt_slide)

    return slides_data


def _build_basic_email(collector):
    """Fallback: build basic email from raw collected data."""
    today = datetime.now().strftime("%Y-%m-%d")
    body = f"안녕하세요,\n\n금주({today})의 2차전지/배터리 업계 동향 리포트를 발송합니다.\n\n"
    body += "=" * 50 + "\n📰 주요 웹 기사\n" + "=" * 50 + "\n\n"
    for i, item in enumerate(collector.web_results[:8], 1):
        body += f"{i}. {item.get('title', 'N/A')}\n"
        body += f"   {item.get('description', '')[:150]}\n"
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

    # 2. Data Collection
    print("\n[Collector] 데이터 수집 중...")
    collector = TrendCollector()
    print("  - 웹 검색 중...")
    collector.collect_web_trends(3)
    print("  - YouTube 검색 중...")
    collector.collect_youtube_trends(3)

    report_content = collector.get_combined_report()
    print(f"[Collector] 웹 {len(collector.web_results)}건, 영상 {len(collector.youtube_results)}건 수집.")

    if args.collect_only:
        print("\nReport Content Preview:")
        print(report_content[:500] + "...")
        return

    # 3. Upload to NotebookLM
    notebook_url = None
    if NOTEBOOK_ID:
        notebook_url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"

    if notebook_url:
        print("\n[Uploader] NotebookLM에 업로드 중...")
        from uploader import NotebookUploader
        uploader = NotebookUploader(notebook_url)
        try:
            uploader.upload_text("Trend Report", report_content)
            print("[Uploader] 업로드 성공!")
        except Exception as e:
            print(f"[Uploader] 업로드 실패: {e}")
            print("[Uploader] 기존 소스로 계속 진행합니다...")

    # 4. Generate Report via NotebookLM
    if notebook_url:
        print("\n[Reporter] 매거진 리포트 생성 중...")
        from reporter import NotebookReporter
        reporter = NotebookReporter(notebook_url)

        prompt = (
            "새로 추가된 자료를 바탕으로 2차전지 업계의 최근 이슈 4가지를 선정하여 심층 분석 리포트를 작성해줘. "
            "각 이슈에 대해 '현황', '주요 원인', '시장 영향', '미래 전망'을 포함하여 자세히 서술할 것. "
            "매거진 특집 기사 스타일로 서론과 에디터 노트도 포함해."
        )
        report_text = reporter.generate_report(prompt)

        if report_text:
            with open("trend_report.md", "w", encoding="utf-8") as f:
                f.write(report_text)

            # PPT via Studio slides
            print("\n[Reporter] Studio Slides PPT 다운로드 중...")
            ppt_file = os.path.join(os.getcwd(), "battery_trend_report_ai.pptx")
            try:
                uploader.download_studio_slides(ppt_file)
                print(f"[PPT] AI PPT 저장 완료: {ppt_file}")
            except Exception as e:
                print(f"[PPT] Studio Slides 실패: {e}, 로컬로 대체...")
                slide_prompt = (
                    "앞서 작성한 4가지 이슈를 바탕으로 PPT 슬라이드 내용을 작성해줘. "
                    "각 이슈마다 슬라이드 1개씩 할당. "
                    "형식:\nTitle: [이슈 제목]\n- [상세 설명 1]\n- [상세 설명 2]..."
                )
                slides_data = reporter.generate_slide_content(slide_prompt)
                if slides_data:
                    from ppt_generator import PPTGenerator
                    ppt_gen = PPTGenerator()
                    ppt_file = ppt_gen.create_presentation(slides_data, "battery_trend_report_local.pptx")

            # Email
            print("\n[Reporter] 이메일 본문 생성 중...")
            summary_prompt = (
                "앞서 작성한 리포트 내용을 바탕으로 이메일 본문을 작성해줘. "
                "정중한 인사말, 핵심 이슈 4가지 요약 (관련 원본 소스 링크 URL 포함), "
                "업계 시사점, 맺음말을 포함할 것."
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
    parser.add_argument('--collect-only', action='store_true', help='Only collect data')
    parser.add_argument('--force-auth', action='store_true', help='Force re-auth')
    parser.add_argument('--cloud', action='store_true', help='Force cloud mode (Gemini API)')
    args = parser.parse_args()

    print("=== ⚡ Battery Trend Reporter ===")

    if args.cloud or is_cloud_env():
        run_cloud_mode()
    else:
        run_local_mode(args)

    print("\n=== ✅ Workflow Complete ===")


if __name__ == "__main__":
    main()
