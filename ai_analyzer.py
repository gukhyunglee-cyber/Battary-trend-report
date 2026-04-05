"""
AI Analyzer Module
Uses Google Gemini API to analyze collected battery trend data
and generate structured report content for PPT and email.
"""
import os
import json
from datetime import datetime

try:
    from google import genai
except ImportError:
    genai = None
    print("[AI] Warning: google-genai not installed. Run: pip install google-genai")


class AIAnalyzer:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY가 설정되지 않았습니다. "
                "환경변수 또는 settings.py에서 설정해주세요."
            )
        if genai is None:
            raise ImportError("google-genai 패키지가 필요합니다: pip install google-genai")

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash"

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API and return text response."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            print(f"[AI] Gemini API 호출 실패: {e}")
            return ""

    def analyze_trends(self, raw_report: str) -> str:
        """
        Analyze collected news data and produce a magazine-style deep analysis.
        Returns the full analysis text in Korean.
        """
        today = datetime.now().strftime("%Y년 %m월 %d일")
        prompt = f"""당신은 2차전지/배터리 산업 전문 애널리스트입니다.

아래는 이번 주에 수집된 배터리 업계 최신 뉴스 및 영상 자료입니다:

---
{raw_report}
---

위 자료를 바탕으로 다음 작업을 수행하세요:

1. **핵심 이슈 4가지를 선정**하세요 (가장 중요하고 영향력 있는 주제 우선)
2. 각 이슈에 대해 다음 항목을 포함한 **심층 분석**을 작성하세요:
   - 현황 (2~3문장)
   - 주요 원인 (2~3문장)
   - 시장 영향 (2~3문장)
   - 미래 전망 (2~3문장)
3. 전체적으로 **매거진 특집 기사 스타일**로 서론과 맺음말도 포함하세요.
4. 관련된 원본 소스의 URL을 반드시 인용하세요.

작성일: {today}
언어: 한국어
톤: Professional, Insightful, Detailed
"""
        print("[AI] Gemini에게 심층 분석 요청 중...")
        result = self._call_gemini(prompt)
        if result:
            print(f"[AI] 분석 완료! ({len(result)} 글자)")
        return result

    def generate_slide_content(self, raw_report: str) -> list:
        """
        Generate structured slide data for PPT creation.
        Returns list of dicts: [{'title': str, 'bullets': [str], 'source_url': str}]
        """
        prompt = f"""당신은 프레젠테이션 전문가입니다.

아래의 배터리 업계 뉴스 데이터를 분석하여, PPT 슬라이드 내용을 JSON 형식으로 생성하세요.

---
{raw_report}
---

요구사항:
1. 핵심 이슈 4가지를 선정하여 각각 1개 슬라이드로 구성
2. 각 슬라이드에는 5~7개의 상세 불릿포인트 포함 (문장 형태)
3. 각 슬라이드에 관련된 소스 URL을 1개 이상 포함

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

```json
[
  {{
    "title": "이슈 제목",
    "bullets": [
      "핵심 내용 1",
      "핵심 내용 2",
      "핵심 내용 3",
      "핵심 내용 4",
      "핵심 내용 5"
    ],
    "source_urls": ["https://example.com/article1"]
  }}
]
```

언어: 한국어
"""
        print("[AI] Gemini에게 슬라이드 콘텐츠 생성 요청 중...")
        result = self._call_gemini(prompt)

        if not result:
            return []

        # Parse JSON from response
        try:
            # Try to extract JSON from markdown code block if present
            if "```json" in result:
                json_str = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                json_str = result.split("```")[1].split("```")[0].strip()
            else:
                json_str = result.strip()

            slides = json.loads(json_str)
            print(f"[AI] 슬라이드 {len(slides)}개 생성 완료!")

            # Convert to ppt_generator format
            formatted = []
            for slide in slides:
                content = list(slide.get("bullets", []))
                urls = slide.get("source_urls", [])
                if urls:
                    content.append("")
                    content.append("📎 출처:")
                    for url in urls:
                        content.append(f"  {url}")

                formatted.append({
                    "title": slide.get("title", "N/A"),
                    "content": content
                })
            return formatted

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            print(f"[AI] JSON 파싱 실패: {e}")
            print(f"[AI] Raw response: {result[:500]}")
            return []

    def generate_email_body(self, raw_report: str, analysis: str = "") -> str:
        """
        Generate a professional email body summarizing the weekly report.
        """
        today = datetime.now().strftime("%Y년 %m월 %d일")
        context = analysis if analysis else raw_report

        prompt = f"""당신은 기업 뉴스레터 작성 전문가입니다.

아래의 이번 주 배터리 업계 분석 내용을 바탕으로 이메일 본문을 작성하세요:

---
{context[:3000]}
---

이메일 구조:
1. 정중한 인사말 (작성일: {today})
2. 금주의 핵심 이슈 4가지 요약 (각 이슈별 핵심 내용 1~2문장 + 관련 원본 소스 URL 링크 반드시 포함)
3. 업계 시사점 (2~3문장)
4. 맺음말

톤: 정중하고 전문적
언어: 한국어
이메일 본문만 출력하세요 (제목, Subject 등은 제외).
"""
        print("[AI] Gemini에게 이메일 본문 생성 요청 중...")
        result = self._call_gemini(prompt)
        if result:
            print(f"[AI] 이메일 본문 생성 완료! ({len(result)} 글자)")
        return result or f"안녕하세요,\n\n{today} 배터리 업계 동향 리포트를 발송합니다.\n상세 내용은 첨부된 PPT를 참조 부탁드립니다.\n\n감사합니다."


if __name__ == "__main__":
    # Quick test
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    analyzer = AIAnalyzer()
    test_data = """
    - Title: 삼성SDI, 전고체 배터리 양산 시작
      URL: https://example.com/1
      Snippet: 삼성SDI가 2026년 전고체 배터리 양산을 시작한다고 발표했다.
    - Title: CATL, 나트륨이온 배터리 가격 혁신
      URL: https://example.com/2
      Snippet: CATL이 나트륨이온 배터리 가격을 kWh당 40달러 이하로 낮추는 데 성공했다.
    """
    print("=== AI 분석 테스트 ===")
    analysis = analyzer.analyze_trends(test_data)
    print(analysis[:500] if analysis else "분석 실패")
