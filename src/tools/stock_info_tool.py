import os
import yfinance as yf
from dotenv import load_dotenv
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from prompts import STOCK_TOOL_DESCRIPTION
import logger


# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Define the stock info function
def get_stock_info(ticker: str) -> str:
    """Fetches current stock price and basic info for a given ticker symbol from Yahoo Finance."""
    logger.info(f"Getting stock info for ticker: {ticker}")
    
    try:
        ticker = ticker.strip().strip("'").strip('"')  # remove any extra quotes
        logger.debug(f"Cleaned ticker: {ticker}")
        
        stock = yf.Ticker(ticker)
        info = stock.info
        current_price = info.get("currentPrice", "N/A")
        name = info.get("longName", "Unknown Company")
        market_cap = info.get("marketCap", "N/A")
        
        result = (
            f"{name} ({ticker.upper()})\n"
            f"Current Price: ${current_price}\n"
            f"Market Cap: {market_cap}"
        )
        
        logger.info(f"Successfully retrieved stock info for {ticker}: {name}, ${current_price}")
        logger.log_tool_call("Stock Info Tool", ticker, result)
        
        return result
    except Exception as e:
        error_msg = f"Error fetching stock info: {str(e)}"
        logger.error(f"Error getting stock info for {ticker}: {str(e)}")
        logger.log_tool_call("Stock Info Tool", ticker, error=error_msg)
        return error_msg

# Define LangChain Tool
stock_tool = Tool(
    name="Stock Info Tool",
    func=get_stock_info,
    description=STOCK_TOOL_DESCRIPTION
)

# === MAIN ===
if __name__ == "__main__":
    # Direct test of the tool
    ticker = "TSLA"
    print("🛠️ Tool test:")
    result = get_stock_info(ticker)
    print(result) 