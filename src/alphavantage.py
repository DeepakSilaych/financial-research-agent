import requests
import pandas as pd
import os
import json
from datetime import datetime, timedelta



def get_stock_data(symbol, function="TIME_SERIES_DAILY", interval="5min", time_period=60, series_type="close", 
                  output_size="compact", datatype="json", adjusted=True, extended_hours=True, 
                  api_key=None, output_format="dataframe", save_csv=False, save_path=None):
    """
    A comprehensive function to fetch stock market data from Alpha Vantage API.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'IBM', 'AAPL')
        function: API function to call - see below for supported functions
        interval: Time interval between data points (1min, 5min, 15min, 30min, 60min, daily, weekly, monthly)
        time_period: Number of data points used for calculations (for technical indicators)
        series_type: Price type for calculations (close, open, high, low)
        output_size: 'compact' for last 100 points, 'full' for full available history
        datatype: Response format from API ('json' or 'csv')
        adjusted: Whether to return adjusted data accounting for splits, dividends, etc.
        extended_hours: Whether to include pre-market and post-market hours
        api_key: Alpha Vantage API key (if None, will check ALPHA_VANTAGE_API_KEY env variable)
        output_format: Return format - 'dataframe', 'dict', or 'raw'
        save_csv: Whether to save the result as CSV
        save_path: Where to save CSV (defaults to current directory/symbol_function.csv)

    Returns:
        Requested market data in the specified format
        
    Supported Functions:
        TIME_SERIES_INTRADAY: Intraday time series (timestamp, open, high, low, close, volume)
        TIME_SERIES_DAILY: Daily time series
        TIME_SERIES_DAILY_ADJUSTED: Daily time series (adjusted for splits/dividends)
        TIME_SERIES_WEEKLY: Weekly time series
        TIME_SERIES_WEEKLY_ADJUSTED: Weekly time series (adjusted)
        TIME_SERIES_MONTHLY: Monthly time series
        TIME_SERIES_MONTHLY_ADJUSTED: Monthly time series (adjusted)
        GLOBAL_QUOTE: Latest price and volume
        SYMBOL_SEARCH: Search for company symbols
        
        Technical Indicators:
        - SMA: Simple Moving Average
        - EMA: Exponential Moving Average
        - MACD: Moving Average Convergence/Divergence
        - RSI: Relative Strength Index
        - BBANDS: Bollinger Bands
        - STOCH: Stochastic Oscillator
        
        Fundamental Data:
        - OVERVIEW: Company information
        - EARNINGS: Annual and quarterly earnings
        - INCOME_STATEMENT: Annual and quarterly income statements
        - BALANCE_SHEET: Annual and quarterly balance sheets
        - CASH_FLOW: Annual and quarterly cash flows
    """
    api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("API key is required. Pass api_key parameter or set ALPHA_VANTAGE_API_KEY environment variable.")
    
    # Base URL
    base_url = "https://www.alphavantage.co/query"
    
    # Parameter mapping for different functions
    params = {
        "function": function,
        "symbol": symbol,
        "apikey": api_key,
        "datatype": datatype
    }
    
    # Add conditional parameters based on function
    if function.startswith("TIME_SERIES_INTRADAY"):
        params["interval"] = interval
        params["outputsize"] = output_size
        params["adjusted"] = "true" if adjusted else "false"
        params["extended_hours"] = "true" if extended_hours else "false"
    elif function in ["TIME_SERIES_DAILY", "TIME_SERIES_WEEKLY", "TIME_SERIES_MONTHLY"]:
        params["outputsize"] = output_size
    elif function.endswith("_ADJUSTED"):
        params["outputsize"] = output_size
    elif function in ["SMA", "EMA", "WMA", "DEMA", "TEMA", "TRIMA", "KAMA", "MAMA", "T3"]:
        params["interval"] = interval
        params["time_period"] = str(time_period)
        params["series_type"] = series_type
    elif function in ["MACD", "MACDEXT", "STOCH", "STOCHF", "RSI", "STOCHRSI", "BBANDS"]:
        params["interval"] = interval
        params["series_type"] = series_type
    
    # Make the API request
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        
        if datatype == "csv":
            if output_format == "raw":
                return response.text
            
            # Save to CSV if requested
            if save_csv:
                file_path = save_path or f"{symbol}_{function}.csv"
                with open(file_path, "w") as f:
                    f.write(response.text)
                
            # Convert to DataFrame if needed
            if output_format == "dataframe":
                import io
                return pd.read_csv(io.StringIO(response.text))
            
            return response.text
        
        # Handle JSON response
        data = response.json()
        
        # Check for errors
        if "Error Message" in data:
            raise ValueError(f"API Error: {data['Error Message']}")
        if "Information" in data:
            print(f"API Information: {data['Information']}")
        if "Note" in data:
            print(f"API Note: {data['Note']}")
            
        # Process different data formats based on function
        if output_format == "raw":
            return data
        elif output_format == "dict":
            return data
        elif output_format == "dataframe":
            # Time Series data
            if any(ts_key in data for ts_key in [
                "Time Series (1min)", "Time Series (5min)", "Time Series (15min)", 
                "Time Series (30min)", "Time Series (60min)", "Time Series (Daily)",
                "Weekly Time Series", "Monthly Time Series", "Weekly Adjusted Time Series",
                "Monthly Adjusted Time Series"
            ]):
                # Find the time series key
                ts_key = [k for k in data.keys() if k.startswith("Time Series") or 
                          k.endswith("Time Series")][0]
                
                # Convert to DataFrame
                df = pd.DataFrame.from_dict(data[ts_key], orient="index")
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # Convert all values to numeric
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col])
                    
                # Rename columns (remove digit prefixes like "1. open")
                df.columns = [col.split(". ")[1] if ". " in col else col for col in df.columns]
                
                if save_csv:
                    file_path = save_path or f"{symbol}_{function}.csv"
                    df.to_csv(file_path)
                
                return df
            
            # Global Quote
            elif "Global Quote" in data:
                quote = data["Global Quote"]
                df = pd.DataFrame([quote])
                
                # Rename columns (remove digit prefixes)
                df.columns = [col.split(". ")[1] if ". " in col else col for col in df.columns]
                
                if save_csv:
                    file_path = save_path or f"{symbol}_{function}.csv"
                    df.to_csv(file_path, index=False)
                    
                return df
                
            # Technical indicators
            elif any(k in data for k in ["Technical Analysis", "Meta Data"]):
                # For technical indicators
                if "Technical Analysis" in data:
                    indicator_key = "Technical Analysis: " + function
                    if indicator_key in data:
                        df = pd.DataFrame.from_dict(data[indicator_key], orient="index")
                        df.index = pd.to_datetime(df.index)
                        df = df.sort_index()
                        
                        # Convert to numeric
                        for col in df.columns:
                            df[col] = pd.to_numeric(df[col])
                        
                        if save_csv:
                            file_path = save_path or f"{symbol}_{function}.csv"
                            df.to_csv(file_path)
                            
                        return df
                
                # Convert all remaining to DataFrame best-effort
                return pd.DataFrame(data)
            
            # Company Overview or other fundamental data
            else:
                # Try different strategies to convert to DataFrame
                try:
                    # If it's a single-level dictionary
                    df = pd.DataFrame([data])
                    if save_csv:
                        file_path = save_path or f"{symbol}_{function}.csv"
                        df.to_csv(file_path, index=False)
                    return df
                except:
                    # Fall back to returning raw data
                    return data
                    
        # Default return raw data
        return data
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"API request failed: {str(e)}")
    except Exception as e:
        raise Exception(f"Error processing data: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Get API key from environment or set directly
    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    api_key = "BAY8O6B5GY36HMB2"
    
    # Example 1: Get daily stock data for IBM
    try:
        daily_data = get_stock_data("IBM", function="TIME_SERIES_DAILY", output_size="compact", 
                                   api_key=api_key, output_format="dataframe")
        print("\nIBM Daily Stock Data (Last 5 days):")
        print(daily_data.tail(5))
    except Exception as e:
        print(f"Error getting daily data: {e}")
        
    # Example 2: Get company overview
    try:
        overview = get_stock_data("AAPL", function="OVERVIEW", api_key=api_key, output_format="dict")
        print("\nApple Inc. Company Overview:")
        for key in ["Symbol", "Name", "Industry", "MarketCapitalization", "PERatio", "DividendYield"]:
            if key in overview:
                print(f"{key}: {overview[key]}")
    except Exception as e:
        print(f"Error getting company overview: {e}")
        
    # Example 3: Get a technical indicator (SMA instead of RSI)
    try:
        # Using SMA (Simple Moving Average) which is available on all API tiers
        sma_data = get_stock_data("MSFT", function="SMA", interval="daily", time_period=20, 
                                 series_type="close", api_key=api_key, output_format="dataframe")
        print("\nMicrosoft SMA (Last 5 days):")
        print(sma_data.tail(5))
    except Exception as e:
        print(f"Error getting SMA data: {e}")
        
    # Example 4: Get latest stock quote (Global Quote)
    try:
        quote = get_stock_data("GOOGL", function="GLOBAL_QUOTE", api_key=api_key, output_format="dict")
        print("\nGoogle (Alphabet) Latest Quote:")
        if "Global Quote" in quote:
            global_quote = quote["Global Quote"]
            for key, value in global_quote.items():
                print(f"{key.replace('01. ', '')}: {value}")
    except Exception as e:
        print(f"Error getting quote data: {e}") 