import os
import pandas as pd
from datetime import datetime, timedelta
import requests
from typing import Optional, List, Dict, Union, Any
from langchain.agents import Tool
from src.prompts import FRED_TOOL_DESCRIPTION
from src.logger import info, warning, error

def get_fred_market_report(indicators: List[str] = None, 
                           time_period: str = "1y",
                           api_key: Optional[str] = None) -> str:
    """
    Generate a comprehensive text-only market report using FRED data.
    
    Args:
        indicators: List of FRED series IDs (defaults to a standard set if None)
        time_period: Time period for analysis ('1m', '3m', '6m', '1y', '5y', '10y')
        api_key: FRED API key (will use environment variable if None)
        
    Returns:
        Text-only report with market analysis
    """
    info(f"Generating FRED market report for time period: {time_period}")
    
    # Use API key from environment if not provided
    api_key = api_key or os.environ.get("FRED_API_KEY")
    
    # Default API key from fred_market_trends.py if needed
    if not api_key:
        api_key = "bb7926bbff5e09d76767573f9b853352"
    
    # Set the time period
    now = datetime.now()
    if time_period == "1m":
        observation_start = (now - timedelta(days=30)).strftime("%Y-%m-%d")
    elif time_period == "3m":
        observation_start = (now - timedelta(days=90)).strftime("%Y-%m-%d")
    elif time_period == "6m":
        observation_start = (now - timedelta(days=180)).strftime("%Y-%m-%d")
    elif time_period == "5y":
        observation_start = (now - timedelta(days=365*5)).strftime("%Y-%m-%d")
    elif time_period == "10y":
        observation_start = (now - timedelta(days=365*10)).strftime("%Y-%m-%d")
    else:  # Default to 1 year
        observation_start = (now - timedelta(days=365)).strftime("%Y-%m-%d")
    
    observation_end = now.strftime("%Y-%m-%d")
    
    # Default indicators if none provided (covering all categories from the request)
    if not indicators:
        indicators = [
            # Macroeconomic Indicators
            "GDP",       # Nominal GDP 
            "GDPC1",     # Real GDP
            "CPIAUCSL",  # CPI
            "UNRATE",    # Unemployment Rate
            "PAYEMS",    # Nonfarm Payrolls
            "CIVPART",   # Labor Force Participation
            
            # Interest Rates & Monetary Policy
            "FEDFUNDS",  # Federal Funds Rate
            "DGS10",     # 10-Year Treasury
            "DGS2",      # 2-Year Treasury
            "T10YIE",    # 5-Year Breakeven Inflation
            "M2SL",      # M2 Money Supply
            
            # Housing & Real Estate
            "HOUST",     # Housing Starts
            "CSUSHPINSA", # Case-Shiller Home Price Index
            "MORTGAGE30US", # 30-Year Mortgage Rate
            
            # Banking & Credit
            "TOTLL",     # Total Loans & Leases
            "DRALACBN",  # Delinquency Rate on Loans
            "MPRIME",    # Bank Prime Loan Rate
            
            # International & Trade
            "DEXUSEU",   # USD/EUR Exchange Rate
            "BOPGSTB",   # Trade Balance
            
            # Consumer & Business Sentiment
            "UMCSENT",   # Consumer Sentiment
            "MANEMP",    # Manufacturing Employment
            "RSAFS",     # Retail Sales
            
            # Financial Markets
            "SP500",     # S&P 500
        ]
    
    # Initialize the report text
    report = f"FRED MARKET INDICATORS REPORT ({time_period.upper()} PERIOD)\n"
    report += "=" * 50 + "\n"
    report += f"Report period: {observation_start} to {observation_end}\n"
    report += f"Generated on: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Create category headers for organization
    categories = {
        "Macroeconomic Indicators": ["GDP", "GDPC1", "CPIAUCSL", "UNRATE", "PAYEMS", "CIVPART"],
        "Interest Rates & Monetary Policy": ["FEDFUNDS", "DGS10", "DGS2", "T10YIE", "M2SL"],
        "Housing & Real Estate": ["HOUST", "CSUSHPINSA", "MORTGAGE30US"],
        "Banking & Credit": ["TOTLL", "DRALACBN", "MPRIME"],
        "International & Trade": ["DEXUSEU", "BOPGSTB"],
        "Consumer & Business Sentiment": ["UMCSENT", "MANEMP", "RSAFS"],
        "Financial Markets": ["SP500"]
    }
    
    # Keep track of indicators we've analyzed
    analyzed_indicators = set()
    
    # Process each category
    for category, category_indicators in categories.items():
        # Check if we have any indicators from this category to report on
        category_indicators_to_analyze = [ind for ind in category_indicators if ind in indicators]
        
        if not category_indicators_to_analyze:
            continue
            
        # Add category header
        report += f"\n{category}\n"
        report += "-" * len(category) + "\n"
        
        # Process each indicator in this category
        for indicator in category_indicators_to_analyze:
            try:
                # Get data from FRED
                info(f"Fetching FRED data for indicator: {indicator}")
                series_data = get_series_observations(
                    series_id=indicator,
                    observation_start=observation_start,
                    observation_end=observation_end,
                    api_key=api_key
                )
                
                if not series_data or "observations" not in series_data or not series_data["observations"]:
                    warning(f"No data available for FRED indicator: {indicator}")
                    report += f"{indicator}: No data available\n\n"
                    continue
                
                # Process observations into a dataframe
                observations = series_data["observations"]
                df = pd.DataFrame(observations)
                
                # Convert to proper types
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                
                # Sort by date (most recent first)
                df = df.sort_values('date', ascending=False)
                
                # Get series info
                series_info = get_series_info(indicator, api_key)
                title = series_info.get("title", indicator)
                units = series_info.get("units", "")
                frequency = series_info.get("frequency", "")
                
                # Add indicator title and basic info
                report += f"{title} ({indicator})\n"
                if units:
                    report += f"Units: {units}\n"
                if frequency:
                    report += f"Frequency: {frequency}\n"
                
                # Latest value
                if not df.empty:
                    latest_date = df.iloc[0]['date'].strftime('%Y-%m-%d')
                    latest_value = df.iloc[0]['value']
                    report += f"Latest value ({latest_date}): {latest_value}\n"
                
                # Add trend analysis
                if len(df) > 1:
                    # Calculate period change
                    first_value = df.iloc[-1]['value']
                    last_value = df.iloc[0]['value']
                    
                    if pd.notna(first_value) and pd.notna(last_value) and first_value != 0:
                        abs_change = last_value - first_value
                        percent_change = (abs_change / first_value) * 100
                        direction = "↑" if percent_change > 0 else "↓"
                        report += f"Change: {direction} {abs(abs_change):.2f} ({abs(percent_change):.2f}%)\n"
                    
                    # Trend direction
                    if len(df) >= 5:
                        values = df.head(5)['value'].values
                        up_count = sum(values[i] > values[i+1] for i in range(len(values)-1))
                        down_count = sum(values[i] < values[i+1] for i in range(len(values)-1))
                        
                        if up_count > down_count:
                            report += "Recent trend: Upward\n"
                        elif down_count > up_count:
                            report += "Recent trend: Downward\n"
                        else:
                            report += "Recent trend: Sideways/Neutral\n"
                
                # Add a summary statistic
                report += f"Summary: "
                
                # Add context based on indicator type
                if indicator in ["GDP", "GDPC1"]:
                    if percent_change > 2:
                        report += "Strong growth above target.\n"
                    elif percent_change > 0:
                        report += "Positive but moderate growth.\n"
                    else:
                        report += "Economic contraction period.\n"
                
                elif indicator in ["CPIAUCSL"]:
                    if percent_change > 4:
                        report += "Inflation substantially above Fed target.\n"
                    elif percent_change > 2:
                        report += "Inflation moderately above Fed target.\n"
                    elif percent_change >= 1.5:
                        report += "Inflation near Fed target.\n"
                    else:
                        report += "Inflation below Fed target.\n"
                
                elif indicator in ["UNRATE"]:
                    if latest_value < 4:
                        report += "Very low unemployment indicates tight labor market.\n"
                    elif latest_value < 5:
                        report += "Unemployment consistent with full employment.\n"
                    elif latest_value < 6:
                        report += "Unemployment slightly elevated.\n"
                    else:
                        report += "High unemployment indicates labor market weakness.\n"
                
                elif indicator in ["FEDFUNDS", "DGS10", "DGS2"]:
                    if percent_change > 1:
                        report += "Significant tightening of monetary conditions.\n"
                    elif percent_change > 0:
                        report += "Modest tightening of monetary conditions.\n"
                    elif percent_change > -1:
                        report += "Modest easing of monetary conditions.\n"
                    else:
                        report += "Significant easing of monetary conditions.\n"
                
                elif indicator in ["HOUST", "CSUSHPINSA"]:
                    if percent_change > 5:
                        report += "Strong growth in housing sector.\n"
                    elif percent_change > 0:
                        report += "Modest growth in housing sector.\n"
                    elif percent_change > -5:
                        report += "Slight contraction in housing sector.\n"
                    else:
                        report += "Significant housing market weakness.\n"
                
                elif indicator in ["SP500"]:
                    if percent_change > 15:
                        report += "Strong bull market conditions.\n"
                    elif percent_change > 5:
                        report += "Positive market momentum.\n"
                    elif percent_change > -5:
                        report += "Sideways market trend.\n"
                    else:
                        report += "Bear market conditions.\n"
                
                else:
                    report += f"Changed by {percent_change:.2f}% over the period.\n"
                
                report += "\n"
                analyzed_indicators.add(indicator)
                
            except Exception as e:
                error(f"Error analyzing FRED indicator {indicator}: {str(e)}")
                report += f"{indicator}: Error retrieving data - {str(e)}\n\n"
    
    # Check for any additional indicators not covered in categories
    remaining_indicators = [ind for ind in indicators if ind not in analyzed_indicators]
    if remaining_indicators:
        report += "\nAdditional Indicators\n"
        report += "-" * 20 + "\n"
        
        for indicator in remaining_indicators:
            try:
                # Get data from FRED
                series_data = get_series_observations(
                    series_id=indicator,
                    observation_start=observation_start,
                    observation_end=observation_end,
                    api_key=api_key
                )
                
                if not series_data or "observations" not in series_data or not series_data["observations"]:
                    report += f"{indicator}: No data available\n\n"
                    continue
                
                # Process observations into a dataframe
                observations = series_data["observations"]
                df = pd.DataFrame(observations)
                
                # Convert to proper types
                df['date'] = pd.to_datetime(df['date'])
                df['value'] = pd.to_numeric(df['value'], errors='coerce')
                
                # Sort by date (most recent first)
                df = df.sort_values('date', ascending=False)
                
                # Get series info
                series_info = get_series_info(indicator, api_key)
                title = series_info.get("title", indicator)
                
                # Add indicator title and basic info
                report += f"{title} ({indicator})\n"
                
                # Latest value
                if not df.empty:
                    latest_date = df.iloc[0]['date'].strftime('%Y-%m-%d')
                    latest_value = df.iloc[0]['value']
                    report += f"Latest value ({latest_date}): {latest_value}\n\n"
                
            except Exception as e:
                error(f"Error analyzing additional FRED indicator {indicator}: {str(e)}")
                report += f"{indicator}: Error retrieving data - {str(e)}\n\n"
    
    report += "\n" + "=" * 50 + "\n"
    report += "End of report\n"
    
    info(f"Completed FRED market report for {time_period} period with {len(analyzed_indicators)} indicators")
    info(f"FRED Market Analysis called with time_period={time_period}, indicators={len(indicators)}")
    
    return report

def get_series_observations(series_id, observation_start=None, observation_end=None, api_key=None):
    """Helper function to get observations for a FRED series"""
    base_url = "https://api.stlouisfed.org/fred"
    observations_url = f"{base_url}/series/observations"
    
    params = {
        "api_key": api_key,
        "series_id": series_id,
        "file_type": "json",
        "sort_order": "desc",
        "limit": 1000
    }
    
    if observation_start:
        params["observation_start"] = observation_start
    if observation_end:
        params["observation_end"] = observation_end
        
    response = requests.get(observations_url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        warning(f"Error fetching FRED data for {series_id}: {response.text}")
        return None

def get_series_info(series_id, api_key):
    """Helper function to get metadata for a FRED series"""
    base_url = "https://api.stlouisfed.org/fred"
    series_url = f"{base_url}/series"
    
    params = {
        "api_key": api_key,
        "series_id": series_id,
        "file_type": "json"
    }
    
    response = requests.get(series_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if "seriess" in data and len(data["seriess"]) > 0:
            return {
                "title": data["seriess"][0].get("title", ""),
                "units": data["seriess"][0].get("units", ""),
                "frequency": data["seriess"][0].get("frequency_short", "")
            }
    
    return {"title": series_id, "units": "", "frequency": ""}

# Define the tools at the end of file
fred_tool = Tool(
    name="FRED Market Analysis",
    func=get_fred_market_report,
    description=FRED_TOOL_DESCRIPTION
)

# Example usage
if __name__ == "__main__":
    # Generate a report for a default set of indicators
    report = get_fred_market_report(time_period="6m")
    print(report)
    
    # Or generate a report for specific indicators
    # specific_indicators = ["SP500", "UNRATE", "CPIAUCSL", "GDP"]
    # specific_report = get_fred_market_report(indicators=specific_indicators, time_period="1y")
    # print(specific_report) 