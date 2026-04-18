"""
Weekly Diff Tracker
Saves weekly snapshots of collected headlines and compares
with the previous week to highlight changes.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SNAPSHOTS_DIR = Path(__file__).parent / "user_data" / "weekly_snapshots"


class WeeklyDiffTracker:
    def __init__(self, snapshots_dir: Path = SNAPSHOTS_DIR):
        self.snapshots_dir = snapshots_dir
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────
    def generate_diff_report(self, current_articles: List[Dict]) -> Tuple[str, bool]:
        """
        Compare current articles with the previous snapshot.
        Save current snapshot and return a tuple: (markdown report, has_new_articles).
        """
        today = datetime.now().strftime("%Y-%m-%d")
        previous = self._load_latest_snapshot()
        self._save_snapshot(today, current_articles)

        if previous is None:
            return self._first_run_report(today, current_articles)

        prev_date, prev_articles = previous
        return self._build_diff(prev_date, prev_articles, today, current_articles)

    # ── Snapshot I/O ───────────────────────────────────────────────────
    def _save_snapshot(self, date_str: str, articles: List[Dict]):
        """Save articles as a dated JSON snapshot."""
        filepath = self.snapshots_dir / f"snapshot_{date_str}.json"
        data = {
            "date": date_str,
            "collected_at": datetime.now().isoformat(),
            "article_count": len(articles),
            "articles": articles,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info(f"[Diff] 스냅샷 저장: {filepath}")

    def _load_latest_snapshot(self) -> Optional[Tuple[str, List[Dict]]]:
        """Load the most recent snapshot file (before today)."""
        files = sorted(self.snapshots_dir.glob("snapshot_*.json"), reverse=True)
        today = datetime.now().strftime("%Y-%m-%d")

        for filepath in files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                snap_date = data.get("date", "")
                # Skip today's snapshot (we want the previous one)
                if snap_date == today:
                    continue
                return snap_date, data.get("articles", [])
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"[Diff] 스냅샷 파싱 실패 ({filepath}): {e}")
                continue

        return None

    # ── Diff logic ─────────────────────────────────────────────────────
    def _build_diff(
        self,
        prev_date: str,
        prev_articles: List[Dict],
        curr_date: str,
        curr_articles: List[Dict],
    ) -> Tuple[str, bool]:
        """Build a markdown diff report comparing two snapshots."""
        # Create lookup sets using (site, title) as unique key
        prev_keys = {(a.get("site", ""), a.get("title", "")) for a in prev_articles}
        curr_keys = {(a.get("site", ""), a.get("title", "")) for a in curr_articles}

        new_keys = curr_keys - prev_keys
        removed_keys = prev_keys - curr_keys

        # Map keys back to full articles
        curr_map = {(a.get("site", ""), a.get("title", "")): a for a in curr_articles}
        prev_map = {(a.get("site", ""), a.get("title", "")): a for a in prev_articles}

        new_articles = [curr_map[k] for k in new_keys if k in curr_map]
        removed_articles = [prev_map[k] for k in removed_keys if k in prev_map]

        # Per-site count changes
        prev_by_site = self._count_by_site(prev_articles)
        curr_by_site = self._count_by_site(curr_articles)
        all_sites = sorted(set(list(prev_by_site.keys()) + list(curr_by_site.keys())))

        # Build report
        lines = [
            f"## 📊 전주 대비 변화 요약 ({curr_date} vs {prev_date})",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🆕 신규 기사 **{len(new_articles)}**건 / ❌ 제거 기사 **{len(removed_articles)}**건",
            f"📰 이번 주 총 **{len(curr_articles)}**건 (전주 {len(prev_articles)}건)",
            "",
        ]

        # Per-site breakdown
        lines.append("### 사이트별 증감")
        for site in all_sites:
            prev_count = prev_by_site.get(site, 0)
            curr_count = curr_by_site.get(site, 0)
            diff = curr_count - prev_count
            if diff > 0:
                indicator = f"🔺+{diff}"
            elif diff < 0:
                indicator = f"🔻{diff}"
            else:
                indicator = "━ 변동없음"
            lines.append(f"- **[{site}]** {prev_count} → {curr_count} ({indicator})")
        lines.append("")

        # New articles detail
        if new_articles:
            lines.append("### 🆕 신규 기사")
            for a in new_articles[:20]:
                lines.append(f"- **[{a['site']}]** {a['title']}")
                lines.append(f"  {a['url']}")
            lines.append("")

        # Removed articles summary
        if removed_articles:
            lines.append("### ❌ 전주에 있었으나 이번 주 미수집 기사")
            for a in removed_articles[:10]:
                lines.append(f"- **[{a['site']}]** {a['title']}")
            if len(removed_articles) > 10:
                lines.append(f"  ... 외 {len(removed_articles) - 10}건")
            lines.append("")

        return "\n".join(lines), len(new_articles) > 0

    def _first_run_report(self, date: str, articles: List[Dict]) -> Tuple[str, bool]:
        """Report for first-time execution (no previous snapshot)."""
        by_site = self._count_by_site(articles)
        lines = [
            f"## 📊 주간 변화 추적 — 초기 스냅샷 ({date})",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"ℹ️ 이전 데이터가 없습니다. 이번 주 데이터를 기준 스냅샷으로 저장합니다.",
            f"📰 총 **{len(articles)}**건 수집",
            "",
            "### 사이트별 수집 현황",
        ]
        for site, count in sorted(by_site.items()):
            lines.append(f"- **[{site}]** {count}건")
        lines.append("")
        lines.append("다음 실행 시 이번 주 데이터와 비교하여 변화를 분석합니다.")
        return "\n".join(lines), True

    @staticmethod
    def _count_by_site(articles: List[Dict]) -> Dict[str, int]:
        counts = {}
        for a in articles:
            site = a.get("site", "기타")
            counts[site] = counts.get(site, 0) + 1
        return counts


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # Quick test with dummy data
    tracker = WeeklyDiffTracker()
    test_articles = [
        {"site": "Battery Technology", "title": "Test Article 1", "url": "https://example.com/1", "category": "업계 미디어", "date": "", "snippet": ""},
        {"site": "Electrive", "title": "Test Article 2", "url": "https://example.com/2", "category": "업계 미디어", "date": "", "snippet": ""},
    ]
    report = tracker.generate_diff_report(test_articles)
    print(report)
