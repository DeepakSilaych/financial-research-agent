#ca66181f410441eeebec77d8cf1f9010
#8d4f34c9addb4a809c5ed5d49ea810f4
from langchain.agents import Tool
import requests

def get_news_from_newsapi(a):
    api_key = "8d4f34c9addb4a809c5ed5d49ea810f4"  # Replace with your NewsAPI key
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": a,     # Search query
        "language": "en",       # English news only
        "sortBy": "publishedAt", # Latest news first
        "pageSize": 5            # Number of articles
    }
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        articles = data.get('articles', [])
        if not articles:
            print("No articles found.")
            return

        for i, article in enumerate(articles):
            print(f"\nArticle {i+1}:")
            print(f"Title: {article.get('title')}")
            print(f"Published At: {article.get('publishedAt')}")
            print(f"Source: {article.get('source', {}).get('name')}")
            print(f"Description: {article.get('description')}")
            print(f"URL: {article.get('url')}")

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


news_tool = Tool(
    name="News Tool",
    func=get_news_from_newsapi,
    description="Use this tool to fetch the latest news articles about a topic. Input should be a keyword like 'Tesla', 'AI', or 'Finance'."
)


# Example usage
if __name__ == "__main__":
    get_news_from_newsapi("Tesla")