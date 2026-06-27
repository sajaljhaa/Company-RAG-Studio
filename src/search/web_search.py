from typing import List, Dict, Any
from duckduckgo_search import DDGS

class WebSearchEngine:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    def search(self, query: str) -> List[Dict[str, str]]:
        """
        Perform a web search using DuckDuckGo.
        Returns a list of dicts: [{'title': ..., 'href': ..., 'body': ...}]
        """
        results = []
        try:
            with DDGS() as ddgs:
                ddg_results = list(ddgs.text(query, max_results=self.max_results))
                for res in ddg_results:
                    results.append({
                        "title": res.get("title", ""),
                        "url": res.get("href", ""),
                        "snippet": res.get("body", "")
                    })
        except Exception as e:
            print(f"Error executing web search for query '{query}': {e}")
        return results

    def find_company_links(self, company_name: str) -> Dict[str, List[str]]:
        """
        Search for main website and career pages for a company.
        """
        main_query = f"{company_name} official website"
        career_query = f"{company_name} careers jobs culture"

        main_results = self.search(main_query)
        career_results = self.search(career_query)

        return {
            "main_links": [r["url"] for r in main_results[:3]],
            "career_links": [r["url"] for r in career_results[:3]]
        }
