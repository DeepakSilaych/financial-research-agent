#ca66181f410441eeebec77d8cf1f9010
#8d4f34c9addb4a809c5ed5d49ea810f4
from langchain.agents import Tool
import requests
from src.prompts import NEWS_TOOL_DESCRIPTION
from src.logger import info, warning, error

def get_news_from_newsapi(query):
    api_key = "8d4f34c9addb4a809c5ed5d49ea810f4"  # Replace with your NewsAPI key
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,     # Search query
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
            return "No articles found."

        result = ""
        for i, article in enumerate(articles):
            result += f"\nArticle {i+1}:\n"
            result += f"Title: {article.get('title')}\n"
            result += f"Published At: {article.get('publishedAt')}\n"
            result += f"Source: {article.get('source', {}).get('name')}\n"
            result += f"Description: {article.get('description')}\n"
            result += f"URL: {article.get('url')}\n"
        
        return result

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        return error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        return error_msg


news_tool = Tool(
    name="News Tool",
    func=get_news_from_newsapi,
    description=NEWS_TOOL_DESCRIPTION
)


# Example usage
if __name__ == "__main__":
    print(get_news_from_newsapi("Tesla")) 