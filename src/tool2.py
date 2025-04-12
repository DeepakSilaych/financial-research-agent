import os
import yfinance as yf
from dotenv import load_dotenv
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_openai import ChatOpenAI


# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Define the stock info function
def get_stock_info(ticker: str) -> str:
    """Fetches current stock price and basic info for a given ticker symbol from Yahoo Finance."""
    try:
        ticker = ticker.strip().strip("'").strip('"')  # remove any extra quotes
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get("currentPrice", "N/A")
        name = info.get("longName", "Unknown Company")
        market_cap = info.get("marketCap", "N/A")
        return (
            f"{name} ({ticker.upper()})\n"
            f"Current Price: ${current_price}\n"
            f"Market Cap: {market_cap}"
        )
    except Exception as e:
        return f"Error fetching stock info: {str(e)}"

# Define LangChain Tool
stock_tool = Tool(
    name="Stock Info Tool",
    func=get_stock_info,
    description="Use this tool to get current stock price and info from Yahoo Finance. Input should be a stock ticker like 'AAPL', 'TSLA', or 'GOOG'."
)

# === MAIN ===
if __name__ == "__main__":
    # Direct test of the tool
    ticker = "TSLA"
    print("🛠️ Tool test:")
    result = get_stock_info(ticker)
    print(result)

