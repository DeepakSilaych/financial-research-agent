from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Optional, List
from src.market_analysis import get_fred_market_report
from src.company_analyzer import analyze_company

class FredMarketReportInput(BaseModel):
    """Input schema for FRED Market Report tool."""
    indicators: Optional[List[str]] = Field(
        None, 
        description="List of FRED series IDs. If not provided, a default set will be used."
    )
    time_period: str = Field(
        "1y", 
        description="Time period for analysis: '1m', '3m', '6m', '1y', '5y', or '10y'"
    )
    api_key: Optional[str] = Field(
        None, 
        description="Your FRED API key. If not provided, will use environment variable."
    )

class FredMarketReportTool(BaseTool):
    """Tool for generating comprehensive market reports using FRED data."""
    name = "fred_market_report"
    description = """
    Generates a text-only comprehensive market analysis report using FRED (Federal Reserve Economic Data).
    
    This tool is useful for:
    1. Analyzing current macroeconomic conditions
    2. Monitoring interest rates and monetary policy
    3. Tracking housing market and real estate trends
    4. Assessing banking and credit conditions
    5. Evaluating international trade and exchange rates
    6. Gauging consumer and business sentiment
    7. Following financial market indicators
    
    Provide a time period and optional list of specific FRED series IDs to analyze.
    """
    args_schema = FredMarketReportInput
    
    def _run(self, indicators: Optional[List[str]] = None, time_period: str = "1y", api_key: Optional[str] = None) -> str:
        """Execute the FRED market report tool."""
        return get_fred_market_report(
            indicators=indicators,
            time_period=time_period,
            api_key=api_key
        )
    
    async def _arun(self, indicators: Optional[List[str]] = None, time_period: str = "1y", api_key: Optional[str] = None) -> str:
        """Execute the FRED market report tool asynchronously."""
        # For simplicity, we're using the sync version in the async method
        # In a production environment, you might want to implement a proper async version
        return self._run(indicators, time_period, api_key)

class CompanyAnalyzerInput(BaseModel):
    """Input schema for Company Analyzer tool."""
    symbol: str = Field(
        ...,  # This makes it required
        description="Stock ticker symbol of the company to analyze (e.g., 'AAPL', 'MSFT', 'GOOGL')"
    )
    api_key: Optional[str] = Field(
        None,
        description="Alpha Vantage API key. If not provided, will use environment variable or default key."
    )

class CompanyAnalyzerTool(BaseTool):
    """Tool for generating comprehensive company analysis reports."""
    name = "company_analyzer"
    description = """
    Generates a comprehensive analysis report for a publicly traded company.
    
    This tool is useful for:
    1. Analyzing a company's financial performance and health
    2. Reviewing stock price history and trends
    3. Examining income statements, balance sheets, and cash flow
    4. Evaluating key financial ratios and metrics
    5. Understanding company valuation and profitability
    6. Tracking earnings history and surprises
    7. Assessing liquidity, solvency, and efficiency ratios
    
    Provide a stock ticker symbol (e.g., 'AAPL' for Apple Inc.) to analyze the company.
    """
    args_schema = CompanyAnalyzerInput
    
    def _run(self, symbol: str, api_key: Optional[str] = None) -> str:
        """Execute the company analyzer tool."""
        return analyze_company(
            symbol=symbol,
            api_key=api_key
        )
    
    async def _arun(self, symbol: str, api_key: Optional[str] = None) -> str:
        """Execute the company analyzer tool asynchronously."""
        # For simplicity, we're using the sync version in the async method
        # In a production environment, you might want to implement a proper async version
        return self._run(symbol, api_key)

# Example usage
if __name__ == "__main__":
    from langchain.agents import initialize_agent, AgentType
    from langchain.llms import OpenAI
    
    # Initialize the tools
    fred_tool = FredMarketReportTool()
    company_tool = CompanyAnalyzerTool()
    
    # Example 1: Direct use of FRED tool
    fred_report = fred_tool.run({"time_period": "3m"})
    print("FRED REPORT SAMPLE:")
    print(fred_report[:500] + "...\n\n")  # Print just the beginning for brevity
    
    # Example 2: Direct use of Company Analyzer tool
    company_report = company_tool.run({"symbol": "AAPL"})
    print("COMPANY REPORT SAMPLE:")
    print(company_report[:500] + "...\n\n")  # Print just the beginning for brevity
    
    # Example 3: Integration with a LangChain agent using both tools
    try:
        llm = OpenAI(temperature=0)
        agent = initialize_agent(
            [fred_tool, company_tool], 
            llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        
        agent_response = agent.run(
            "First give me an analysis of recent GDP and unemployment data, then analyze Apple Inc."
        )
        print(agent_response)
    except Exception as e:
        print(f"Agent example requires OpenAI API key: {str(e)}") 