"""
Orchestrator Module
Manages the full workflow: Collect -> Check Auth -> Upload -> Generate Report
"""
import sys
import os
import argparse
from pathlib import Path

# Fix for Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import local modules
from collector import TrendCollector
from uploader import NotebookUploader
from settings import NOTEBOOK_ID, NOTEBOOK_NAME

# auth_manager is in project root (copied from skills)
from auth_manager import AuthManager

def main():
    parser = argparse.ArgumentParser(description='Battery Trend Reporter Orchestrator')
    parser.add_argument('--collect-only', action='store_true', help='Only collect data, do not upload')
    parser.add_argument('--force-auth', action='store_true', help='Force re-authentication')
    args = parser.parse_args()

    print("=== Battery Trend Reporter ===")
    
    # 1. Authentication Check
    if not args.collect_only:
        auth = AuthManager()
        if args.force_auth or not auth.is_authenticated():
            print("\n[Auth] Authentication required.")
            print("Starting authentication setup...")
            if auth.setup_auth(headless=False):
                print("[Auth] Successfully authenticated!")
            else:
                print("[Auth] Authentication failed.")
                return
    else:
        print("\n[Auth] Skipping authentication check (collect-only mode).")

    # 2. Data Collection
    print("\n[Collector] Gathering data...")
    collector = TrendCollector()
    
    print("  - Searching Web...")
    collector.collect_web_trends(3)
    
    print("  - Searching YouTube...")
    collector.collect_youtube_trends(3)
    
    report_content = collector.get_combined_report()
    print(f"\n[Collector] Collected {len(collector.web_results)} web items and {len(collector.youtube_results)} videos.")
    
    if args.collect_only:
        print("\nReport Content Preview:")
        print(report_content[:500] + "...")
        print("\nSkipping upload as requested.")
        return

    # 3. Upload to NotebookLM
    print("\n[Uploader] Uploading to NotebookLM...")
    
    notebook_url = None
    if NOTEBOOK_ID:
        notebook_url = f"https://notebooklm.google.com/notebook/{NOTEBOOK_ID}"
    else:
        # Check if we should create a new notebook or if user provided one manually
        print("[Uploader] No Notebook ID found in settings.")
        
        # Instantiate uploader without URL first to use create_notebook
        temp_uploader = NotebookUploader("")
        try:
            notebook_url = temp_uploader.create_notebook(NOTEBOOK_NAME)
            # Extract ID from URL for future use (optional, could save to settings)
            # URL format: .../notebook/ID
            new_id = notebook_url.split("/")[-1]
            print(f"[Uploader] Created new notebook! ID: {new_id}")
            print(f"           URL: {notebook_url}")
            print(f"           Please update settings.py with NOTEBOOK_ID = '{new_id}' to reuse it.")
            
            # Re-instantiate with correct URL
            uploader = NotebookUploader(notebook_url)
        except Exception as e:
            print(f"[Uploader] Failed to create notebook: {e}")
            return
            
    if notebook_url:
        uploader = NotebookUploader(notebook_url)
        try:
            uploader.upload_text(f"Trend Report - {os.path.basename(__file__)}", report_content)
            print("[Uploader] Successfully uploaded source!")
        except Exception as e:
            print(f"[Uploader] Warning: Failed to upload: {e}")
            print("[Uploader] Continuing with existing sources...")
            # return # Do not return, continue to reporting

    # 4. Generate Magazine Report
    print("\n[Reporter] Generating Magazine Report...")
    # NOTE: Since we reused the browser context in uploader, we should potentially reuse it here too.
    # But reporter spawns its own context. This is fine as long as they don't conflict (sequential).
    
    if notebook_url:
        from reporter import NotebookReporter
        reporter = NotebookReporter(notebook_url)
        
        # Korean Prompts
        # 1. Magazine Report
        prompt = (
            "새로 추가된 자료를 바탕으로 2차전지 업계의 최근 이슈 4가지를 선정하여 심층 분석 리포트를 작성해줘. "
            "각 이슈에 대해 '현황', '주요 원인', '시장 영향', '미래 전망'을 포함하여 자세히 서술할 것. "
            "매거진 특집 기사 스타일로 서론과 에디터 노트도 포함해. Tone: Professional, Insightful, Detailed."
        )
        report_text = reporter.generate_report(prompt)
        
        if report_text:
            print("\n" + "="*40)
            print("GENERATED REPORT")
            print("="*40)
            print(report_text)
            print("="*40)
            
            # Save report to file
            with open("trend_report.md", "w", encoding="utf-8") as f:
                f.write(report_text)

            # 2. PPT Generation via NotebookLM Studio
            print("\n[Reporter] Downloading Studio Slides PPT...")
            ppt_file = os.path.join(os.getcwd(), "battery_trend_report_ai.pptx")
            try:
                # Use the uploader instance to download slides
                uploader.download_studio_slides(ppt_file)
                print(f"[PPT] AI Presentation saved to {ppt_file}")
            except Exception as e:
                print(f"[PPT] Failed to download AI slides: {e}")
                print("[PPT] Falling back to local PPT generator...")
                
                slide_prompt = (
                    "앞서 작성한 4가지 이슈를 바탕으로 PPT 슬라이드 내용을 작성해줘. "
                    "각 이슈마다 슬라이드 1개씩 할당하고, 내용을 풍부하게 작성할 것. "
                    "각 슬라이드 당 5~7개의 상세한 불렛포인트(문장 형태)를 포함해줘. "
                    "형식:\nTitle: [이슈 제목]\n- [상세 설명 1]\n- [상세 설명 2]..."
                )
                slides_data = reporter.generate_slide_content(slide_prompt)
                
                if slides_data:
                    from ppt_generator import PPTGenerator
                    ppt_gen = PPTGenerator()
                    ppt_file = ppt_gen.create_presentation(slides_data, "battery_trend_report_local.pptx")
                    print(f"[PPT] Local fallback presentation saved to {ppt_file}")
                else:
                    print("[PPT] Failed to generate local slide content fallback.")
                    ppt_file = None

            # 3. Email Body Summary
            print("\n[Reporter] Generating Email Summary...")
            summary_prompt = (
                "앞서 작성한 리포트 내용을 바탕으로 이메일 본문을 작성해줘. "
                "다음 구조를 갖출 것:\n"
                "1. 정중한 인사말\n"
                "2. 금주의 핵심 이슈 4가지 요약 (각 이슈별 핵심 내용 1~2문장 및 관련된 원본 소스/정보입수처 링크 URL 반드시 포함)\n"
                "3. 업계 시사점\n"
                "4. 맺음말"
            )
            email_body = reporter.generate_email_summary(summary_prompt)
            if not email_body:
                 email_body = "리포트가 첨부되었습니다."

            # 4. Email Report
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
                print("[Mailer] No recipient configured in settings.py")
        else:
            print("[Reporter] Failed to generate report.")

    print("\n=== Workflow Complete ===")

if __name__ == "__main__":
    main()
