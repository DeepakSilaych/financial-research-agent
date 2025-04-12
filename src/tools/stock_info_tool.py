import os
import yfinance as yf
import logging
import pandas as pd
from dotenv import load_dotenv
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('finance_agent')

# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Helper function to format values
def format_value(value, is_percentage=False, is_currency=False, in_millions=False):
    if value is None or value == "N/A":
        return "N/A"
    
    if in_millions and isinstance(value, (int, float)):
        value = value / 1000000
        return f"${value:.2f}M"
    
    if is_percentage and isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    
    if is_currency and isinstance(value, (int, float)):
        return f"${value:.2f}"
    
    return value

# Core stock information function
def get_stock_info(ticker: str) -> str:
    """Fetches comprehensive stock information for a given ticker symbol."""
    logger.info(f"Getting stock info for ticker: {ticker}")
    
    try:
        ticker = ticker.strip().strip("'").strip('"')
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Basic info
        name = info.get("longName", "Unknown Company")
        current_price = format_value(info.get("currentPrice"), is_currency=True)
        market_cap = format_value(info.get("marketCap"))
        
        # Valuation metrics
        pe_ratio = format_value(info.get("trailingPE"))
        pb_ratio = format_value(info.get("priceToBook"))
        ps_ratio = format_value(info.get("priceToSalesTrailing12Months"))
        
        # Profitability metrics
        eps = format_value(info.get("trailingEps"), is_currency=True)
        roe = format_value(info.get("returnOnEquity"), is_percentage=True)
        
        # Dividend information
        dividend_yield = format_value(info.get("dividendYield"), is_percentage=True)
        
        # Debt metrics
        debt_to_equity = format_value(info.get("debtToEquity"))
        
        # Analyst recommendations
        target_price = format_value(info.get("targetMeanPrice"), is_currency=True)
        recommendation = info.get("recommendationKey", "N/A")
        if recommendation:
            recommendation = recommendation.capitalize()
        
        result = (
            f"{name} ({ticker.upper()})\n"
            f"Current Price: {current_price}\n"
            f"Market Cap: {market_cap}\n\n"
            f"Valuation Metrics:\n"
            f"P/E Ratio: {pe_ratio}\n"
            f"P/B Ratio: {pb_ratio}\n"
            f"P/S Ratio: {ps_ratio}\n\n"
            f"Profitability:\n"
            f"EPS (TTM): {eps}\n"
            f"Return on Equity: {roe}\n\n"
            f"Dividend Yield: {dividend_yield}\n"
            f"Debt-to-Equity: {debt_to_equity}\n\n"
            f"Analyst Target Price: {target_price}\n"
            f"Recommendation: {recommendation}"
        )
        
        logger.info(f"Successfully retrieved stock info for {ticker}")
        return result
    except Exception as e:
        error_msg = f"Error fetching stock info: {str(e)}"
        logger.error(f"Error getting stock info for {ticker}: {str(e)}")
        return error_msg

# Financial statements function
def get_financial_statements(ticker: str, statement_type: str = "income") -> str:
    """Fetches financial statements for a given ticker."""
    logger.info(f"Getting {statement_type} statement for ticker: {ticker}")
    
    try:
        ticker = ticker.strip().strip("'").strip('"')
        stock = yf.Ticker(ticker)
        
        if statement_type.lower() == "income":
            statement = stock.income_stmt
            statement_name = "Income Statement"
        elif statement_type.lower() == "balance":
            statement = stock.balance_sheet
            statement_name = "Balance Sheet"
        elif statement_type.lower() == "cash":
            statement = stock.cashflow
            statement_name = "Cash Flow Statement"
        else:
            return "Invalid statement type. Choose 'income', 'balance', or 'cash'."
        
        if statement.empty:
            return f"No {statement_name} data available for {ticker.upper()}"
        
        # Format the statement for readability - show key metrics only
        result = f"{statement_name} for {ticker.upper()} (in millions):\n\n"
        
        # Select key metrics based on statement type
        if statement_type.lower() == "income":
            key_metrics = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income']
        elif statement_type.lower() == "balance":
            key_metrics = ['Total Assets', 'Total Liabilities', 'Total Equity']
        else:  # Cash flow
            key_metrics = ['Operating Cash Flow', 'Capital Expenditure', 'Free Cash Flow']
        
        # Extract and format the data
        for metric in key_metrics:
            for index in statement.index:
                if metric.lower() in str(index).lower():
                    result += f"{index}:\n"
                    for col in statement.columns:
                        value = statement.loc[index, col]/1000000  # Convert to millions
                        result += f"  {col.strftime('%Y-%m-%d')}: ${value:.2f}M\n"
                    result += "\n"
        
        return result
    except Exception as e:
        error_msg = f"Error fetching {statement_type} statement: {str(e)}"
        logger.error(f"Error getting {statement_type} statement for {ticker}: {str(e)}")
        return error_msg

# Historical performance function
def get_historical_performance(ticker: str, period: str = "1y") -> str:
    """Gets historical performance data for a specified period."""
    logger.info(f"Getting historical performance for ticker: {ticker} over period: {period}")
    
    try:
        ticker = ticker.strip().strip("'").strip('"')
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return f"No historical data available for {ticker.upper()} over period {period}"
        
        # Calculate performance metrics
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        performance = ((end_price - start_price) / start_price) * 100
        
        # Calculate high and low
        period_high = hist['High'].max()
        period_low = hist['Low'].min()
        
        # Calculate volatility
        volatility = hist['Close'].pct_change().std() * 100
        
        result = (
            f"Historical Performance for {ticker.upper()} over {period}:\n"
            f"Start Price: ${start_price:.2f}\n"
            f"End Price: ${end_price:.2f}\n"
            f"Performance: {performance:.2f}%\n"
            f"Period High: ${period_high:.2f}\n"
            f"Period Low: ${period_low:.2f}\n"
            f"Volatility: {volatility:.2f}%"
        )
        
        return result
    except Exception as e:
        error_msg = f"Error fetching historical performance: {str(e)}"
        logger.error(f"Error getting historical performance for {ticker}: {str(e)}")
        return error_msg

# Technical indicators function
def get_technical_indicators(ticker: str) -> str:
    """Calculates technical indicators for a given ticker."""
    logger.info(f"Getting technical indicators for ticker: {ticker}")
    
    try:
        ticker = ticker.strip().strip("'").strip('"')
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return f"No historical data available for {ticker.upper()}"
        
        # Calculate moving averages
        hist['SMA50'] = hist['Close'].rolling(window=50).mean()
        hist['SMA200'] = hist['Close'].rolling(window=200).mean()
        
        # Calculate RSI
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # Get the most recent values
        current_close = hist['Close'].iloc[-1]
        sma50 = hist['SMA50'].iloc[-1]
        sma200 = hist['SMA200'].iloc[-1]
        rsi = hist['RSI'].iloc[-1]
        
        # Determine trend signals
        trend = "Bullish" if current_close > sma50 > sma200 else "Bearish" if current_close < sma50 < sma200 else "Mixed"
        rsi_signal = "Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Neutral"
        
        result = (
            f"Technical Indicators for {ticker.upper()}:\n"
            f"Current Price: ${current_close:.2f}\n"
            f"50-Day SMA: ${sma50:.2f}\n"
            f"200-Day SMA: ${sma200:.2f}\n"
            f"RSI (14-Day): {rsi:.2f} - {rsi_signal}\n"
            f"Overall Trend: {trend}"
        )
        
        return result
    except Exception as e:
        error_msg = f"Error calculating technical indicators: {str(e)}"
        logger.error(f"Error getting technical indicators for {ticker}: {str(e)}")
        return error_msg

# Define LangChain Tools
stock_tool = Tool(
    name="Stock Info Tool",
    func=get_stock_info,
    description="Fetches current stock price and comprehensive financial metrics for a given ticker symbol."
)

financial_statements_tool = Tool(
    name="Financial Statements Tool",
    func=get_financial_statements,
    description="Retrieves income statement, balance sheet, or cash flow statement data for a company. Specify the ticker and statement type ('income', 'balance', or 'cash')."
)

historical_performance_tool = Tool(
    name="Historical Performance Tool",
    func=get_historical_performance,
    description="Retrieves historical price data and calculates performance over a specified time period. Specify the ticker and period (e.g., '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')."
)

technical_indicators_tool = Tool(
    name="Technical Indicators Tool",
    func=get_technical_indicators,
    description="Calculates technical indicators like moving averages and RSI for a given ticker symbol."
)


# === MAIN ===
if __name__ == "__main__":
    # Test the finance agent
    ticker = "AAPL"
    
    print("\n🛠️ Testing Stock Info Tool:")
    print(get_stock_info(ticker))
    
    print("\n🛠️ Testing Financial Statements Tool:")
    print(get_financial_statements(ticker, "income"))
    
    print("\n🛠️ Testing Historical Performance Tool:")
    print(get_historical_performance(ticker, "1y"))
    
    print("\n🛠️ Testing Technical Indicators Tool:")
    print(get_technical_indicators(ticker))
    
