"""
Orchestrator Module
Manages the full workflow: Collect -> Report -> Email
Supports two modes:
  - Cloud mode (GitHub Actions): collect + local PPT + email (no NotebookLM)
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
    Cloud mode: No browser / no NotebookLM.
    Collect data -> build PPT from raw data -> email.
    """
    print("\n[Mode] Cloud mode (GitHub Actions)")

    # 1. Collect
    print("\n[Collector] Gathering data...")
    collector = TrendCollector()
    print("  - Searching Web...")
    collector.collect_web_trends(5)
    print("  - Searching YouTube...")
    collector.collect_youtube_trends(3)

    report_content = collector.get_combined_report()
    total = len(collector.web_results) + len(collector.youtube_results)
    print(f"[Collector] Collected {total} items total.")

    if total == 0:
        print("[Collector] No data collected. Aborting.")
        sys.exit(1)

    # Save raw report
    with open("trend_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)

    # 2. Build PPT from collected data
    print("\n[PPT] Generating presentation from collected data...")
    from ppt_generator import PPTGenerator

    slides_data = []
    # Group web results into slides (1 slide per topic keyword group)
    from settings import SEARCH_KEYWORDS_KR
    for i, kw in enumerate(SEARCH_KEYWORDS_KR):
        matching = [r for r in collector.web_results
                    if any(word in (r.get('title', '') + r.get('description', ''))
                           for word in kw.split())]
        if not matching:
            continue
        slide = {
            'title': kw,
            'content': []
        }
        for r in matching[:4]:
            title = r.get('title', 'N/A')
            url = r.get('url', '')
            desc = r.get('description', '')[:120]
            slide['content'].append(f"{title}")
            slide['content'].append(f"  {desc}")
            slide['content'].append(f"  Link: {url}")
        slides_data.append(slide)

    # Add YouTube slide
    if collector.youtube_results:
        yt_slide = {
            'title': 'YouTube - 배터리 관련 최신 영상',
            'content': []
        }
        for v in collector.youtube_results[:5]:
            yt_slide['content'].append(f"{v.get('title', 'N/A')}")
            yt_slide['content'].append(f"  {v.get('url', '')}")
        slides_data.append(yt_slide)

    ppt_file = None
    if slides_data:
        ppt_gen = PPTGenerator()
        ppt_file = ppt_gen.create_presentation(slides_data, "battery_trend_report.pptx")
        print(f"[PPT] Saved to {ppt_file}")
    else:
        print("[PPT] No slides data generated.")

    # 3. Build email body from collected data
    print("\n[Email] Building email body...")
    today = datetime.now().strftime("%Y-%m-%d")
    email_body = f"안녕하세요,\n\n금주({today})의 2차전지/배터리 업계 동향 리포트를 발송합니다.\n\n"
    email_body += "=" * 50 + "\n"
    email_body += "📰 주요 웹 기사\n"
    email_body += "=" * 50 + "\n\n"

    for i, item in enumerate(collector.web_results[:8], 1):
        email_body += f"{i}. {item.get('title', 'N/A')}\n"
        email_body += f"   {item.get('description', '')[:150]}\n"
        email_body += f"   🔗 {item.get('url', '')}\n\n"

    if collector.youtube_results:
        email_body += "=" * 50 + "\n"
        email_body += "🎬 관련 YouTube 영상\n"
        email_body += "=" * 50 + "\n\n"
        for i, v in enumerate(collector.youtube_results[:5], 1):
            email_body += f"{i}. {v.get('title', 'N/A')}\n"
            email_body += f"   🔗 {v.get('url', '')}\n\n"

    email_body += "상세 내용은 첨부된 PPT를 참조 부탁드립니다.\n감사합니다.\n"

    # 4. Send email
    print("\n[Mailer] Sending email...")
    from mailer import EmailSender
    from settings import EMAIL_RECIPIENT

    if EMAIL_RECIPIENT:
        mailer = EmailSender()
        subject = f"[Weekly] Battery Trend Report ({today})"
        if mailer.send_email(EMAIL_RECIPIENT, subject, email_body, attachment_path=ppt_file):
            print("[Mailer] Email sent successfully!")
        else:
            print("[Mailer] Failed to send email.")
            sys.exit(1)
    else:
        print("[Mailer] No recipient configured.")
        sys.exit(1)


def run_local_mode(args):
    """
    Local mode: Uses NotebookLM for AI-powered report generation.
    """
    print("\n[Mode] Local mode (with NotebookLM)")

    from auth_manager import AuthManager

    # 1. Authentication Check
    auth = AuthManager()
    if args.force_auth or not auth.is_authenticated():
        print("\n[Auth] Authentication required.")
        if auth.setup_auth(headless=False):
            print("[Auth] Successfully authenticated!")
        else:
            print("[Auth] Authentication failed.")
            return

    # 2. Data Collection
    print("\n[Collector] Gathering data...")
    collector = TrendCollector()
    print("  - Searching Web...")
    collector.collect_web_trends(3)
    print("  - Searching YouTube...")
    collector.collect_youtube_trends(3)

    report_content = collector.get_combined_report()
    print(f"[Collector] Collected {len(collector.web_results)} web, {len(collector.youtube_results)} videos.")

    if args.collect_only:
        print("\nReport Content Preview:")
        print(report_content[:500] + "...")
        return

    # 3. Upload to NotebookLM
    notebook_url = None
    if NOTEBOOK_ID:
        notebook_url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"

    if notebook_url:
        print("\n[Uploader] Uploading to NotebookLM...")
        from uploader import NotebookUploader
        uploader = NotebookUploader(notebook_url)
        try:
            uploader.upload_text(f"Trend Report", report_content)
            print("[Uploader] Successfully uploaded!")
        except Exception as e:
            print(f"[Uploader] Warning: Failed to upload: {e}")
            print("[Uploader] Continuing with existing sources...")

    # 4. Generate Report via NotebookLM
    if notebook_url:
        print("\n[Reporter] Generating Magazine Report...")
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
            print("\n[Reporter] Downloading Studio Slides PPT...")
            ppt_file = os.path.join(os.getcwd(), "battery_trend_report_ai.pptx")
            try:
                uploader.download_studio_slides(ppt_file)
                print(f"[PPT] AI Presentation saved to {ppt_file}")
            except Exception as e:
                print(f"[PPT] AI slides failed: {e}, using local fallback...")
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
            print("\n[Reporter] Generating Email Summary...")
            summary_prompt = (
                "앞서 작성한 리포트 내용을 바탕으로 이메일 본문을 작성해줘. "
                "정중한 인사말, 핵심 이슈 4가지 요약 (관련 원본 소스 링크 URL 포함), "
                "업계 시사점, 맺음말을 포함할 것."
            )
            email_body = reporter.generate_email_summary(summary_prompt) or "리포트가 첨부되었습니다."

            print("\n[Mailer] Sending Report via Email...")
            from mailer import EmailSender
            from settings import EMAIL_RECIPIENT

            if EMAIL_RECIPIENT:
                mailer = EmailSender()
                subject = f"Battery Trend Report (Weekly)"
                if mailer.send_email(EMAIL_RECIPIENT, subject, email_body, attachment_path=ppt_file):
                    print("[Mailer] Email sent successfully.")
                else:
                    print("[Mailer] Failed to send email.")
            else:
                print("[Mailer] No recipient configured.")
        else:
            print("[Reporter] Failed to generate report.")


def main():
    parser = argparse.ArgumentParser(description='Battery Trend Reporter')
    parser.add_argument('--collect-only', action='store_true', help='Only collect data')
    parser.add_argument('--force-auth', action='store_true', help='Force re-auth')
    parser.add_argument('--cloud', action='store_true', help='Force cloud mode (no NotebookLM)')
    args = parser.parse_args()

    print("=== Battery Trend Reporter ===")

    if args.cloud or is_cloud_env():
        run_cloud_mode()
    else:
        run_local_mode(args)

    print("\n=== Workflow Complete ===")


if __name__ == "__main__":
    main()
