"""
Trend Collector Module
Collects battery trend headlines directly from 10 target sites
via RSS feeds and HTML scraping (no DuckDuckGo dependency).
"""
import logging
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from settings import TARGET_SITES

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Shared HTTP session for connection pooling
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
})

REQUEST_TIMEOUT = 15  # seconds


class TrendCollector:
    def __init__(self):
        self.results: List[Dict] = []

    # ── Public API ─────────────────────────────────────────────────────
    def collect_from_sites(self, max_per_site: int = 10) -> List[Dict]:
        """Iterate through all TARGET_SITES and collect headlines."""
        logging.info(f"=== 10개 사이트에서 헤드라인 수집 시작 ===")
        self.results = []

        for site in TARGET_SITES:
            name = site["name"]
            logging.info(f"[{name}] 수집 중...")
            try:
                articles = self._collect_one_site(site, max_per_site)
                self.results.extend(articles)
                logging.info(f"[{name}] {len(articles)}건 수집 완료")
            except Exception as e:
                logging.error(f"[{name}] 수집 실패: {e}")
            time.sleep(1)  # polite delay

        logging.info(f"=== 총 {len(self.results)}건 수집 완료 ===")
        return self.results

    def get_combined_report(self) -> str:
        """Format collected data into a text report."""
        report = f"--- Battery Trend Report ({datetime.now().strftime('%Y-%m-%d')}) ---\n"
        report += f"총 {len(self.results)}건 수집 (10개 사이트)\n\n"

        # Group by category
        categories = {}
        for item in self.results:
            cat = item.get("category", "기타")
            categories.setdefault(cat, []).append(item)

        for cat, items in categories.items():
            report += f"### [{cat}]\n"
            for item in items:
                report += f"- **[{item['site']}]** {item['title']}\n"
                report += f"  URL: {item['url']}\n"
                if item.get("date"):
                    report += f"  Date: {item['date']}\n"
                if item.get("snippet"):
                    report += f"  Snippet: {item['snippet'][:200]}\n"
                report += "\n"

        return report

    # ── Internal: per-site collection ──────────────────────────────────
    def _collect_one_site(self, site: Dict, max_items: int) -> List[Dict]:
        """Try RSS first, then fall back to HTML scraping."""
        articles = []

        # 1) Try RSS if available
        if site.get("rss_url"):
            articles = self._parse_rss(site, max_items)

        # 2) Fallback to HTML scraping
        if not articles:
            articles = self._scrape_html(site, max_items)

        return articles

    # ── RSS parsing ────────────────────────────────────────────────────
    def _parse_rss(self, site: Dict, max_items: int) -> List[Dict]:
        """Parse an RSS/Atom feed and return article dicts."""
        rss_url = site["rss_url"]
        try:
            resp = _SESSION.get(rss_url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            logging.warning(f"[{site['name']}] RSS 요청 실패 ({rss_url}): {e}")
            return []

        articles = []
        try:
            root = ET.fromstring(resp.content)
            # Handle both RSS 2.0 (<item>) and Atom (<entry>) feeds
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)

            for item in items[:max_items]:
                title = self._xml_text(item, "title", ns)
                link = (
                    self._xml_text(item, "link", ns)
                    or self._xml_attr(item, "link", "href", ns)
                )
                date = (
                    self._xml_text(item, "pubDate", ns)
                    or self._xml_text(item, "updated", ns)
                    or self._xml_text(item, "atom:updated", ns)
                )
                snippet = (
                    self._xml_text(item, "description", ns)
                    or self._xml_text(item, "atom:summary", ns)
                    or ""
                )
                # Clean HTML from snippet
                if snippet:
                    snippet = BeautifulSoup(snippet, "html.parser").get_text(strip=True)

                if title and link:
                    articles.append({
                        "site": site["name"],
                        "category": site["category"],
                        "title": title.strip(),
                        "url": link.strip(),
                        "date": (date or "").strip(),
                        "snippet": snippet[:300],
                    })
        except ET.ParseError as e:
            logging.warning(f"[{site['name']}] RSS 파싱 에러: {e}")

        return articles

    # ── HTML scraping ──────────────────────────────────────────────────
    def _scrape_html(self, site: Dict, max_items: int) -> List[Dict]:
        """Scrape headlines from the site's main page using common patterns."""
        url = site["url"]
        try:
            resp = _SESSION.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except Exception as e:
            logging.warning(f"[{site['name']}] HTML 요청 실패 ({url}): {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = []

        # Strategy: find headline links in common containers
        # Priority order of selectors
        candidates = self._extract_candidates(soup, url)

        seen_titles = set()
        for title, link in candidates:
            title = title.strip()
            if not title or len(title) < 10 or title in seen_titles:
                continue
            seen_titles.add(title)
            articles.append({
                "site": site["name"],
                "category": site["category"],
                "title": title,
                "url": link,
                "date": "",
                "snippet": "",
            })
            if len(articles) >= max_items:
                break

        return articles

    def _extract_candidates(self, soup: BeautifulSoup, base_url: str):
        """Extract (title, url) pairs from common HTML patterns."""
        candidates = []

        # 1) <article> elements with heading links
        for article in soup.find_all("article"):
            for heading in article.find_all(["h1", "h2", "h3", "h4"]):
                link_tag = heading.find("a", href=True)
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    href = urljoin(base_url, link_tag["href"])
                    candidates.append((title, href))

        # 2) Heading tags with links (outside articles)
        if len(candidates) < 3:
            for heading in soup.find_all(["h2", "h3"]):
                link_tag = heading.find("a", href=True)
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    href = urljoin(base_url, link_tag["href"])
                    candidates.append((title, href))

        # 3) Links in common news containers
        if len(candidates) < 3:
            for container_class in ["news", "post", "article", "card", "item", "entry", "media-body"]:
                for div in soup.find_all(class_=lambda c: c and container_class in c.lower()):
                    for a in div.find_all("a", href=True):
                        text = a.get_text(strip=True)
                        if text and len(text) > 15:
                            href = urljoin(base_url, a["href"])
                            candidates.append((text, href))

        return candidates

    # ── XML helpers ────────────────────────────────────────────────────
    @staticmethod
    def _xml_text(element, tag: str, ns: dict) -> Optional[str]:
        """Get text from an XML element, trying with and without namespace."""
        el = element.find(tag)
        if el is not None and el.text:
            return el.text
        # try with atom namespace
        el = element.find(f"atom:{tag}", ns)
        if el is not None and el.text:
            return el.text
        return None

    @staticmethod
    def _xml_attr(element, tag: str, attr: str, ns: dict) -> Optional[str]:
        """Get attribute from an XML element."""
        el = element.find(tag)
        if el is not None:
            return el.get(attr)
        el = element.find(f"atom:{tag}", ns)
        if el is not None:
            return el.get(attr)
        return None


if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    collector = TrendCollector()
    print("=== 10개 사이트 헤드라인 수집 테스트 ===\n")
    results = collector.collect_from_sites(max_per_site=5)

    print(f"\n총 {len(results)}건 수집됨\n")
    for r in results[:20]:
        print(f"  [{r['site']}] {r['title'][:60]}")
        print(f"    → {r['url']}")

    print("\n=== 리포트 출력 ===\n")
    print(collector.get_combined_report()[:2000])
