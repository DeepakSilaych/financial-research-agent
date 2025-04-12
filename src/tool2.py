import requests
import os
from typing import List, Dict, Any, Optional

def web_search(query: str) -> List[Dict[str, Any]]:
    
    api_key = os.getenv("TAVILY_API_KEY")
    api_key = "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"
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")
    
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "include_domains": [],
        "exclude_domains": []
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json().get("results", [])
        print("=== Web Search Results for query: ", query, " ===")
        print(results)
        print("=== End of Web Search Results ===")
        return results
    except requests.exceptions.RequestException as e:
        print(f"Error performing web search: {e}")
        return []

if __name__ == "__main__":
    web_search("copper price")