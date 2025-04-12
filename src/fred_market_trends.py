import requests
import pandas as pd
import os
import json
from datetime import datetime, timedelta


def get_market_trends(series_id=None, category_id=None, search_text=None, 
                     observation_start=None, observation_end=None, 
                     api_key=None, output_format='dataframe', 
                     limit=1000, save_csv=False, save_path=None):
    """
    Retrieves market trend data from FRED API (Federal Reserve Economic Data).
    
    Args:
        series_id: FRED series ID (e.g., 'GDP', 'UNRATE', 'SP500')
        category_id: FRED category ID to retrieve series from 
        search_text: Keywords to search for series
        observation_start: Start date for observations (YYYY-MM-DD)
        observation_end: End date for observations (YYYY-MM-DD)
        api_key: FRED API key (if None, will use environment variable)
        output_format: Format for output ('dataframe', 'dict', or 'raw')
        limit: Maximum number of results to return
        save_csv: Whether to save results as CSV
        save_path: Path to save CSV file
        
    Returns:
        Market trend data in requested format
    """
    api_key = api_key or os.environ.get("FRED_API_KEY")
    api_key = "bb7926bbff5e09d76767573f9b853352"
    if not api_key:
        raise ValueError("FRED API key is required. Set it as FRED_API_KEY environment variable or pass directly.")
    
    base_url = "https://api.stlouisfed.org/fred"
    result = {}
    
    # Search for series if text is provided
    if search_text and not series_id:
        search_url = f"{base_url}/series/search"
        params = {
            "api_key": api_key,
            "search_text": search_text,
            "limit": limit,
            "file_type": "json"
        }
        
        response = requests.get(search_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error searching for series: {response.text}")
        
        search_results = response.json()
        if output_format == 'dataframe' and search_results.get('seriess'):
            result['search_results'] = pd.DataFrame(search_results['seriess'])
        else:
            result['search_results'] = search_results
        
        # Use the first series ID if available
        if search_results.get('seriess') and len(search_results['seriess']) > 0:
            series_id = search_results['seriess'][0]['id']
            print(f"Using first search result: {series_id} - {search_results['seriess'][0]['title']}")
    
    # Get data for a specific category
    if category_id and not series_id:
        category_url = f"{base_url}/category/series"
        params = {
            "api_key": api_key,
            "category_id": category_id,
            "limit": limit,
            "file_type": "json"
        }
        
        response = requests.get(category_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error getting category series: {response.text}")
        
        category_results = response.json()
        if output_format == 'dataframe' and category_results.get('seriess'):
            result['category_series'] = pd.DataFrame(category_results['seriess'])
        else:
            result['category_series'] = category_results
        
        # Use the first series ID if available
        if category_results.get('seriess') and len(category_results['seriess']) > 0:
            series_id = category_results['seriess'][0]['id']
            print(f"Using first category series: {series_id} - {category_results['seriess'][0]['title']}")
    
    # Get series observations if we have a series ID
    if series_id:
        # First get series information
        series_url = f"{base_url}/series"
        params = {
            "api_key": api_key,
            "series_id": series_id,
            "file_type": "json"
        }
        
        response = requests.get(series_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error getting series info: {response.text}")
        
        series_info = response.json()
        result['series_info'] = series_info
        
        # Then get observations
        observations_url = f"{base_url}/series/observations"
        params = {
            "api_key": api_key,
            "series_id": series_id,
            "file_type": "json",
            "sort_order": "desc",
            "limit": limit
        }
        
        # Add date parameters if provided
        if observation_start:
            params["observation_start"] = observation_start
        if observation_end:
            params["observation_end"] = observation_end
            
        response = requests.get(observations_url, params=params)
        if response.status_code != 200:
            raise Exception(f"Error getting observations: {response.text}")
        
        observations = response.json()
        
        # Format observations as dataframe if requested
        if output_format == 'dataframe' and observations.get('observations'):
            df = pd.DataFrame(observations['observations'])
            # Convert date strings to datetime
            df['date'] = pd.to_datetime(df['date'])
            # Convert values to float where possible
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            result['observations'] = df
            
            # Save to CSV if requested
            if save_csv:
                save_path = save_path or f"fred_{series_id}_{datetime.now().strftime('%Y%m%d')}.csv"
                df.to_csv(save_path, index=False)
                print(f"Data saved to {save_path}")
                
            # Create a formatted text summary
            if len(df) > 0:
                title = series_info.get('seriess', [{}])[0].get('title', 'Unknown Series')
                units = series_info.get('seriess', [{}])[0].get('units', '')
                frequency = series_info.get('seriess', [{}])[0].get('frequency', '')
                
                result['summary'] = {
                    'title': title,
                    'id': series_id,
                    'units': units,
                    'frequency': frequency,
                    'earliest_date': df['date'].min().strftime('%Y-%m-%d'),
                    'latest_date': df['date'].max().strftime('%Y-%m-%d'),
                    'min_value': df['value'].min(),
                    'max_value': df['value'].max(),
                    'latest_value': df.iloc[0]['value'] if not df.empty else None,
                    'num_observations': len(df)
                }
        else:
            result['observations'] = observations
    
    # Return different formats based on output_format
    if output_format == 'raw':
        return result
    elif output_format == 'dataframe':
        return result
    else:  # dict format
        return result

def get_market_categories():
    """
    Returns a list of common market trend categories in FRED with their IDs.
    """
    return {
        "Money, Banking, & Finance": 32991,
        "National Accounts": 32992,
        "Production & Business Activity": 32993,
        "International Data": 32264,
        "Prices": 32995,
        "Population, Employment, & Labor Markets": 32996,
        "Housing": 32997,
        "Stock Markets": 32255,
        "Interest Rates": 22,
        "Exchange Rates": 95,
        "Consumer Sentiment": 98
    }

def get_popular_market_indicators():
    """
    Returns a dictionary of popular market indicators and their FRED series IDs.
    """
    return {
        "GDP (Quarterly)": "GDP",
        "Real GDP (Quarterly)": "GDPC1",
        "GDP Growth Rate (Quarterly)": "A191RL1Q225SBEA",
        "Unemployment Rate": "UNRATE",
        "CPI (All Items)": "CPIAUCSL",
        "Core CPI (All Items Less Food and Energy)": "CPILFESL",
        "Inflation Rate": "T10YIE",
        "Federal Funds Rate": "FEDFUNDS",
        "10-Year Treasury Rate": "GS10",
        "S&P 500": "SP500",
        "Dow Jones Industrial Average": "DJIA",
        "NASDAQ Composite": "NASDAQCOM",
        "US Dollar Index": "DTWEXBGS",
        "Consumer Sentiment": "UMCSENT",
        "Industrial Production": "INDPRO",
        "Retail Sales": "RSAFS",
        "Housing Starts": "HOUST",
        "M2 Money Supply": "M2SL"
    }

def analyze_market_trends(indicator_name=None, series_id=None, observation_start=None, 
                         observation_end=None, api_key=None):
    """
    Analyzes market trends for a given indicator.
    
    Args:
        indicator_name: Name of the indicator from popular_market_indicators
        series_id: FRED series ID (alternative to indicator_name)
        observation_start: Start date for analysis (YYYY-MM-DD)
        observation_end: End date for analysis (YYYY-MM-DD)
        api_key: FRED API key
        
    Returns:
        Formatted analysis of the market trend
    """
    indicators = get_popular_market_indicators()
    
    # If indicator name is provided, get the series ID
    if indicator_name and indicator_name in indicators:
        series_id = indicators[indicator_name]
    elif not series_id:
        raise ValueError("Either indicator_name or series_id must be provided")
    
    # Default to looking back 1 year if no dates specified
    if not observation_start:
        observation_start = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    if not observation_end:
        observation_end = datetime.now().strftime("%Y-%m-%d")
    
    # Get the data
    result = get_market_trends(
        series_id=series_id,
        observation_start=observation_start,
        observation_end=observation_end,
        api_key=api_key,
        output_format='dataframe'
    )
    
    if 'observations' not in result or result['observations'].empty:
        return f"No data available for series {series_id}"
    
    # Get the data and info
    df = result['observations']
    info = result.get('summary', {})
    
    # Create a text analysis
    analysis = f"MARKET TREND ANALYSIS: {info.get('title', series_id)}\n"
    analysis += "=" * 50 + "\n\n"
    
    # Basic information
    analysis += f"Series ID: {series_id}\n"
    analysis += f"Units: {info.get('units', 'N/A')}\n"
    analysis += f"Frequency: {info.get('frequency', 'N/A')}\n"
    analysis += f"Period: {info.get('earliest_date', 'N/A')} to {info.get('latest_date', 'N/A')}\n\n"
    
    # Latest value
    analysis += f"Latest value ({df.iloc[0]['date'].strftime('%Y-%m-%d')}): {df.iloc[0]['value']}\n"
    
    # Change calculations
    if len(df) > 1:
        # Calculate period change
        first_value = df.iloc[-1]['value']
        last_value = df.iloc[0]['value']
        
        if first_value and first_value != 0:
            percent_change = ((last_value - first_value) / first_value) * 100
            analysis += f"Change over period: {last_value - first_value:.2f} ({percent_change:.2f}%)\n"
        
        # Calculate short-term trends (last 5 observations)
        if len(df) >= 5:
            short_term = df.head(5)
            short_term_change = ((short_term.iloc[0]['value'] - short_term.iloc[-1]['value']) / 
                               short_term.iloc[-1]['value']) * 100
            analysis += f"Recent trend (last 5 observations): {short_term_change:.2f}%\n"
        
        # Calculate if trending up or down over last 10 observations
        if len(df) >= 10:
            recent = df.head(10)
            # Simple trend detection
            values = recent['value'].values
            up_moves = sum(values[i] > values[i+1] for i in range(len(values)-1))
            down_moves = sum(values[i] < values[i+1] for i in range(len(values)-1))
            
            if up_moves > down_moves:
                analysis += "Direction: Upward trend\n"
            elif down_moves > up_moves:
                analysis += "Direction: Downward trend\n"
            else:
                analysis += "Direction: Sideways/Neutral\n"
    
    # Statistical summary
    analysis += f"\nStatistical Summary:\n"
    analysis += f"Minimum: {info.get('min_value', 'N/A')}\n"
    analysis += f"Maximum: {info.get('max_value', 'N/A')}\n"
    analysis += f"Average: {df['value'].mean():.2f}\n"
    analysis += f"Median: {df['value'].median():.2f}\n"
    analysis += f"Standard Deviation: {df['value'].std():.2f}\n"
    
    # Year-over-year comparison if data is available
    if len(df) > 12 and 'date' in df.columns:
        one_year_ago = datetime.now() - timedelta(days=365)
        year_ago_data = df[df['date'] <= one_year_ago].iloc[0]
        if not year_ago_data.empty:
            current = df.iloc[0]['value']
            year_ago = year_ago_data['value']
            yoy_change = ((current - year_ago) / year_ago) * 100
            analysis += f"\nYear-over-year change: {yoy_change:.2f}%\n"
    
    # Add some market context based on the type of indicator
    indicator_type = None
    if "GDP" in series_id:
        indicator_type = "economic_growth"
    elif "UNRATE" in series_id or "PAYEMS" in series_id:
        indicator_type = "employment"
    elif "CPI" in series_id or "PCE" in series_id:
        indicator_type = "inflation"
    elif "FEDFUNDS" in series_id or "GS10" in series_id:
        indicator_type = "interest_rates"
    elif "SP500" in series_id or "DJIA" in series_id or "NASDAQ" in series_id:
        indicator_type = "stock_market"
    
    if indicator_type:
        analysis += f"\nMarket Context:\n"
        if indicator_type == "economic_growth":
            analysis += "GDP is a key indicator of economic health. Growth above 2-3% annually is generally considered strong.\n"
        elif indicator_type == "employment":
            analysis += "The unemployment rate reflects labor market conditions. Rates below 5% typically suggest a tight labor market.\n"
        elif indicator_type == "inflation":
            analysis += "CPI measures price changes. The Federal Reserve targets inflation of around 2% over the long run.\n"
        elif indicator_type == "interest_rates":
            analysis += "Interest rates impact borrowing costs and economic activity. Higher rates can slow economic growth.\n"
        elif indicator_type == "stock_market":
            analysis += "Stock indices reflect market sentiment and economic expectations. They can be leading indicators.\n"
    
    analysis += f"\n{'=' * 50}\n"
    analysis += f"Analysis generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return analysis

# Example usage
if __name__ == "__main__":
    # Uncomment and use any of these examples
    
    # Example 1: Get S&P 500 data
    # result = get_market_trends(series_id="SP500", limit=100)
    # if 'observations' in result:
    #     print(f"Retrieved {len(result['observations'])} observations for S&P 500")
    #     print(result['observations'].head())
    
    # Example 2: Search for GDP series
    # result = get_market_trends(search_text="GDP", limit=5)
    # if 'search_results' in result:
    #     print(f"Found {len(result['search_results'])} GDP-related series")
    #     print(result['search_results'])
    
    # Example 3: Analyze inflation trends
    analysis = analyze_market_trends(indicator_name="CPI (All Items)")
    print(analysis)
    
    # Example 4: Get stock market data
    analysis = analyze_market_trends(indicator_name="S&P 500")
    print(analysis) 