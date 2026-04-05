"""
Trend Collector Module
Collects battery trend information from Web and YouTube using DuckDuckGo
"""
import logging
import time
from typing import List, Dict
from duckduckgo_search import DDGS
from settings import SEARCH_KEYWORDS_KR, YOUTUBE_KEYWORDS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TrendCollector:
    def __init__(self):
        self.web_results = []
        self.youtube_results = []
        # specific: Initialize DDGS once might timeout, better to init per request or handle robustly
        # But for now, simple init
        self.ddgs = DDGS()

    def collect_web_trends(self, num_results: int = 3) -> List[Dict]:
        """Search Web for battery trends"""
        logging.info("Searching Web for battery trends...")
        results = []
        
        for keyword in SEARCH_KEYWORDS_KR:
            logging.info(f"Querying: {keyword}")
            try:
                # DDGS().text() returns an iterator
                # max_results is supported in recent versions
                ddg_gen = self.ddgs.text(keyword, max_results=num_results, region='kr-kr')
                
                count = 0
                for item in ddg_gen:
                    if count >= num_results:
                        break
                    results.append({
                        "source": "Web",
                        "title": item.get('title'),
                        "url": item.get('href'),
                        "description": item.get('body')
                    })
                    count += 1
                time.sleep(1) # Polite delay
            except Exception as e:
                logging.error(f"Error searching for {keyword}: {e}")
                
        self.web_results = results
        return results

    def collect_youtube_trends(self, limit: int = 3) -> List[Dict]:
        """Search YouTube videos via DuckDuckGo"""
        logging.info("Searching YouTube for battery trends...")
        results = []

        for keyword in YOUTUBE_KEYWORDS:
            logging.info(f"Querying YouTube: {keyword}")
            try:
                # DDGS().videos() returns an iterator
                ddg_gen = self.ddgs.videos(keyword, max_results=limit, region='kr-kr')
                
                count = 0
                for video in ddg_gen:
                    if count >= limit:
                        break
                    # DDGS video result usually has 'content' as URL or 'href'
                    # Result structure: {'content': 'https://www.youtube.com/watch?v=...', 'title': '...', 'description': '...', ...}
                    url = video.get('content') or video.get('href')
                    
                    if url and ('youtube.com' in url or 'youtu.be' in url):
                        results.append({
                            "source": "YouTube",
                            "title": video.get('title'),
                            "url": url,
                            "description": f"Published: {video.get('published')} | {video.get('description')}",
                            "published": video.get('published')
                        })
                        count += 1
                        
                time.sleep(1)
            except Exception as e:
                logging.error(f"Error searching YouTube for {keyword}: {e}")

        self.youtube_results = results
        return results

    def get_combined_report(self) -> str:
        """Format collected data into a text report for NotebookLM"""
        report = "--- Battery Trend Report Sources ---\n\n"
        
        report += "### Web Articles\n"
        for item in self.web_results:
            report += f"- Title: {item['title']}\n"
            report += f"  URL: {item['url']}\n"
            report += f"  Snippet: {item['description']}\n\n"
            
        report += "### YouTube Videos\n"
        for item in self.youtube_results:
            report += f"- Title: {item['title']}\n"
            report += f"  URL: {item['url']}\n"
            report += f"  Info: {item.get('description', '')}\n\n"
            
        return report

if __name__ == "__main__":
    import sys
    # Fix for Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    collector = TrendCollector()
    print("Collecting Web Trends...")
    collector.collect_web_trends(2)
    print("Collecting YouTube Trends...")
    collector.collect_youtube_trends(2)
    
    print("\nGenerated Report:\n")
    print(collector.get_combined_report())
