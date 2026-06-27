import re
import urllib.parse
from typing import List, Dict, Set, Any
import httpx
from bs4 import BeautifulSoup
import trafilatura

class CompanyCrawler:
    CAREER_KEYWORDS = ["career", "careers", "job", "jobs", "join-us", "work-with-us", "culture", "openings", "positions"]
    ABOUT_KEYWORDS = ["about", "about-us", "company", "team", "mission", "values", "product", "products"]

    def __init__(self, max_pages: int = 15, timeout: float = 10.0):
        self.max_pages = max_pages
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _normalize_url(self, url: str) -> str:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        return url.rstrip("/")

    def _get_domain(self, url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc

    def _classify_url(self, url: str) -> str:
        lower_url = url.lower()
        if any(keyword in lower_url for keyword in self.CAREER_KEYWORDS):
            return "career_page"
        return "main_website"

    def crawl_company(self, start_url: str, extra_urls: List[str] = None) -> List[Dict[str, Any]]:
        """
        Crawl main company website and career pages.
        """
        start_url = self._normalize_url(start_url)
        domain = self._get_domain(start_url)
        
        urls_to_visit: List[str] = [start_url]
        if extra_urls:
            for extra in extra_urls:
                norm_extra = self._normalize_url(extra)
                if norm_extra not in urls_to_visit:
                    urls_to_visit.append(norm_extra)

        visited_urls: Set[str] = set()
        crawled_documents: List[Dict[str, Any]] = []

        with httpx.Client(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
            while urls_to_visit and len(crawled_documents) < self.max_pages:
                current_url = urls_to_visit.pop(0)
                if current_url in visited_urls:
                    continue

                visited_urls.add(current_url)

                try:
                    response = client.get(current_url)
                    if response.status_code != 200:
                        continue

                    html_content = response.text
                    
                    # Extract text using trafilatura
                    extracted_text = trafilatura.extract(html_content, include_links=False, include_images=False)
                    
                    # Parse page title
                    soup = BeautifulSoup(html_content, "html.parser")
                    title_tag = soup.find("title")
                    title = title_tag.get_text().strip() if title_tag else current_url

                    content_type = self._classify_url(current_url)

                    if extracted_text and len(extracted_text.strip()) > 100:
                        crawled_documents.append({
                            "url": current_url,
                            "title": title,
                            "content_type": content_type,
                            "content": extracted_text,
                            "domain": domain
                        })

                    # Discover more links within same domain
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        full_url = urllib.parse.urljoin(current_url, href)
                        parsed_full = urllib.parse.urlparse(full_url)

                        # Check same domain and HTTP/HTTPS protocol
                        if parsed_full.netloc == domain and parsed_full.scheme in ["http", "https"]:
                            clean_url = full_url.split("#")[0].rstrip("/")
                            if clean_url not in visited_urls and clean_url not in urls_to_visit:
                                # Prioritize career and about pages
                                lower_clean = clean_url.lower()
                                is_priority = any(k in lower_clean for k in self.CAREER_KEYWORDS + self.ABOUT_KEYWORDS)
                                if is_priority:
                                    urls_to_visit.insert(0, clean_url)
                                else:
                                    urls_to_visit.append(clean_url)

                except Exception as e:
                    print(f"Error crawling {current_url}: {e}")

        return crawled_documents
