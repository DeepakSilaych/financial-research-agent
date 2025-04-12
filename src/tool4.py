import requests
import pandas as pd
import os
import json
from datetime import datetime, timedelta
from langchain.agents import Tool

def analyze_company(symbol, api_key=None):
    """
    Fetches and returns comprehensive data about a company from Alpha Vantage API.
    
    Args:
        symbol: Company stock ticker symbol (e.g., 'AAPL', 'MSFT', 'GOOGL')
        api_key: Alpha Vantage API key (if None, will use environment variable)
        
    Returns:
        Comprehensive company data as formatted text
    """
    api_key = api_key or os.environ.get("ALPHA_VANTAGE_API_KEY") or "BAY8O6B5GY36HMB2"
    base_url = "https://www.alphavantage.co/query"
    result_text = f"COMPREHENSIVE ANALYSIS FOR: {symbol}\n{'=' * 50}\n\n"
    
    # Store data for calculating ratios later
    all_data = {}
    
    # Define all data points we want to fetch
    data_points = [
        {"function": "OVERVIEW", "title": "COMPANY OVERVIEW"},
        {"function": "GLOBAL_QUOTE", "title": "CURRENT STOCK PRICE"},
        {"function": "TIME_SERIES_DAILY", "title": "DAILY STOCK PRICES (Last 100 Days)"},
        {"function": "SMA", "params": {"interval": "daily", "time_period": "50", "series_type": "close"}, 
         "title": "SIMPLE MOVING AVERAGE (50-Day)"},
        {"function": "EMA", "params": {"interval": "daily", "time_period": "20", "series_type": "close"}, 
         "title": "EXPONENTIAL MOVING AVERAGE (20-Day)"},
        {"function": "INCOME_STATEMENT", "title": "INCOME STATEMENT"},
        {"function": "BALANCE_SHEET", "title": "BALANCE SHEET"},
        {"function": "CASH_FLOW", "title": "CASH FLOW"},
        {"function": "EARNINGS", "title": "EARNINGS"},
    ]
    
    for data_point in data_points:
        try:
            # Prepare request parameters
            params = {
                "function": data_point["function"],
                "symbol": symbol,
                "apikey": api_key
            }
            
            # Add any additional parameters
            if "params" in data_point:
                params.update(data_point["params"])
                
            # Make API request
            response = requests.get(base_url, params=params)
            data = response.json()
            
            # Store the data for ratio calculations
            all_data[data_point["function"]] = data
            
            # Check for errors
            if "Error Message" in data:
                result_text += f"\n{data_point['title']}\n{'-' * 30}\n"
                result_text += f"Error: {data['Error Message']}\n"
                continue
            
            if "Information" in data:
                result_text += f"Note: {data['Information']}\n"
                continue
                
            if "Note" in data:
                result_text += f"API Limit Note: {data['Note']}\n"
            
            # Format data based on the function
            result_text += f"\n{data_point['title']}\n{'-' * 30}\n"
            
            # Company Overview
            if data_point["function"] == "OVERVIEW":
                important_fields = [
                    "Symbol", "Name", "Description", "Exchange", "Industry", "Sector",
                    "MarketCapitalization", "PERatio", "PEGRatio", "BookValue", "DividendPerShare",
                    "DividendYield", "EPS", "RevenuePerShareTTM", "ProfitMargin", "QuarterlyEarningsGrowthYOY",
                    "QuarterlyRevenueGrowthYOY", "AnalystTargetPrice", "52WeekHigh", "52WeekLow"
                ]
                
                for field in important_fields:
                    if field in data:
                        # Format monetary values
                        if field in ["MarketCapitalization"]:
                            try:
                                value = float(data[field])
                                if value >= 1e9:
                                    formatted_value = f"${value/1e9:.2f} billion"
                                elif value >= 1e6:
                                    formatted_value = f"${value/1e6:.2f} million"
                                else:
                                    formatted_value = f"${value:,.2f}"
                                result_text += f"{field}: {formatted_value}\n"
                            except:
                                result_text += f"{field}: {data[field]}\n"
                        # Format percentages
                        elif field in ["DividendYield", "ProfitMargin", "QuarterlyEarningsGrowthYOY", "QuarterlyRevenueGrowthYOY"]:
                            try:
                                value = float(data[field])
                                result_text += f"{field}: {value*100:.2f}%\n"
                            except:
                                result_text += f"{field}: {data[field]}\n"
                        # Other values
                        else:
                            result_text += f"{field}: {data[field]}\n"
                            
            # Global Quote
            elif data_point["function"] == "GLOBAL_QUOTE":
                if "Global Quote" in data:
                    quote = data["Global Quote"]
                    result_text += f"Symbol: {quote.get('01. symbol', 'N/A')}\n"
                    result_text += f"Price: ${quote.get('05. price', 'N/A')}\n"
                    result_text += f"Change: {quote.get('09. change', 'N/A')} ({quote.get('10. change percent', 'N/A')})\n"
                    result_text += f"Volume: {quote.get('06. volume', 'N/A')}\n"
                    result_text += f"Latest Trading Day: {quote.get('07. latest trading day', 'N/A')}\n"
                    
            # Time Series Data
            elif data_point["function"].startswith("TIME_SERIES"):
                # Find the time series key
                ts_key = next((k for k in data.keys() if k.startswith("Time Series") or k.endswith("Time Series")), None)
                
                if ts_key:
                    # Convert to DataFrame for easier handling
                    df = pd.DataFrame.from_dict(data[ts_key], orient="index")
                    df.index = pd.to_datetime(df.index)
                    df = df.sort_index(ascending=False) # Most recent first
                    
                    # Display only the last 10 days
                    result_text += "Recent price data (last 10 days):\n"
                    for date, row in df.head(10).iterrows():
                        date_str = date.strftime("%Y-%m-%d")
                        try:
                            open_price = float(row.get('1. open', row.get('open', 0)))
                            high_price = float(row.get('2. high', row.get('high', 0)))
                            low_price = float(row.get('3. low', row.get('low', 0)))
                            close_price = float(row.get('4. close', row.get('close', 0)))
                            volume = int(float(row.get('5. volume', row.get('volume', 0))))
                            
                            result_text += f"{date_str}: Open ${open_price:.2f}, Close ${close_price:.2f}, "
                            result_text += f"High ${high_price:.2f}, Low ${low_price:.2f}, Volume {volume:,}\n"
                        except:
                            result_text += f"{date_str}: {dict(row)}\n"
                    
                    # Add summary statistics
                    if len(df) > 0:
                        result_text += "\nSummary Statistics:\n"
                        try:
                            latest_close = float(df.iloc[0].get('4. close', df.iloc[0].get('close', 0)))
                            highest_price = df['2. high' if '2. high' in df.columns else 'high'].astype(float).max()
                            lowest_price = df['3. low' if '3. low' in df.columns else 'low'].astype(float).min()
                            avg_volume = df['5. volume' if '5. volume' in df.columns else 'volume'].astype(float).mean()
                            
                            result_text += f"Latest Close: ${latest_close:.2f}\n"
                            result_text += f"Highest Price (100 days): ${highest_price:.2f}\n"
                            result_text += f"Lowest Price (100 days): ${lowest_price:.2f}\n"
                            result_text += f"Average Volume: {avg_volume:,.0f}\n"
                        except:
                            result_text += "Could not calculate summary statistics\n"
                
            # Technical Indicators (SMA, EMA, etc.)
            elif data_point["function"] in ["SMA", "EMA", "MACD", "RSI", "BBANDS"]:
                # Find the technical indicator key
                indicator_key = next((k for k in data.keys() if k.startswith("Technical Analysis")), None)
                
                if indicator_key:
                    # Convert to DataFrame for easier handling
                    df = pd.DataFrame.from_dict(data[indicator_key], orient="index")
                    df.index = pd.to_datetime(df.index)
                    df = df.sort_index(ascending=False) # Most recent first
                    
                    # Display the last 10 values
                    result_text += f"Recent {data_point['function']} values (last 10 days):\n"
                    for date, row in df.head(10).iterrows():
                        date_str = date.strftime("%Y-%m-%d")
                        for col, val in row.items():
                            try:
                                val_float = float(val)
                                result_text += f"{date_str}: {col}: ${val_float:.2f}\n"
                            except:
                                result_text += f"{date_str}: {col}: {val}\n"
                
            # Financial Statements
            elif data_point["function"] in ["INCOME_STATEMENT", "BALANCE_SHEET", "CASH_FLOW"]:
                if "annualReports" in data and "quarterlyReports" in data:
                    # First show the most recent annual report
                    if data["annualReports"]:
                        annual = data["annualReports"][0] # Most recent annual report
                        result_text += f"Most Recent Annual Report (Fiscal Year: {annual.get('fiscalDateEnding', 'N/A')}):\n"
                        
                        # Select important fields based on the statement type
                        if data_point["function"] == "INCOME_STATEMENT":
                            important_fields = [
                                "totalRevenue", "grossProfit", "operatingIncome", "netIncome", 
                                "ebitda", "eps"
                            ]
                        elif data_point["function"] == "BALANCE_SHEET":
                            important_fields = [
                                "totalAssets", "totalCurrentAssets", "cashAndCashEquivalentsAtCarryingValue",
                                "totalLiabilities", "totalCurrentLiabilities", "totalShareholderEquity", 
                                "treasuryStock"
                            ]
                        elif data_point["function"] == "CASH_FLOW":
                            important_fields = [
                                "operatingCashflow", "cashflowFromInvestment", "cashflowFromFinancing",
                                "dividendPayout", "netIncome"
                            ]
                        
                        for field in important_fields:
                            if field in annual:
                                try:
                                    value = float(annual[field])
                                    if abs(value) >= 1e9:
                                        formatted_value = f"${value/1e9:.2f} billion"
                                    elif abs(value) >= 1e6:
                                        formatted_value = f"${value/1e6:.2f} million"
                                    else:
                                        formatted_value = f"${value:,.2f}"
                                    result_text += f"{field}: {formatted_value}\n"
                                except:
                                    result_text += f"{field}: {annual[field]}\n"
                        
                    # Then show the most recent quarterly report
                    if data["quarterlyReports"]:
                        quarterly = data["quarterlyReports"][0] # Most recent quarterly report
                        result_text += f"\nMost Recent Quarterly Report (Quarter Ending: {quarterly.get('fiscalDateEnding', 'N/A')}):\n"
                        
                        for field in important_fields:
                            if field in quarterly:
                                try:
                                    value = float(quarterly[field])
                                    if abs(value) >= 1e9:
                                        formatted_value = f"${value/1e9:.2f} billion"
                                    elif abs(value) >= 1e6:
                                        formatted_value = f"${value/1e6:.2f} million"
                                    else:
                                        formatted_value = f"${value:,.2f}"
                                    result_text += f"{field}: {formatted_value}\n"
                                except:
                                    result_text += f"{field}: {quarterly[field]}\n"
            
            # Earnings
            elif data_point["function"] == "EARNINGS":
                if "annualEarnings" in data and len(data["annualEarnings"]) > 0:
                    result_text += "Annual Earnings (Last 5 Years):\n"
                    for i, earning in enumerate(data["annualEarnings"][:5]):
                        result_text += f"Fiscal Year Ending {earning.get('fiscalDateEnding', 'N/A')}: "
                        try:
                            eps = float(earning.get('reportedEPS', 0))
                            result_text += f"EPS ${eps:.2f}\n"
                        except:
                            result_text += f"EPS {earning.get('reportedEPS', 'N/A')}\n"
                
                if "quarterlyEarnings" in data and len(data["quarterlyEarnings"]) > 0:
                    result_text += "\nQuarterly Earnings (Last 4 Quarters):\n"
                    for i, earning in enumerate(data["quarterlyEarnings"][:4]):
                        result_text += f"Quarter Ending {earning.get('fiscalDateEnding', 'N/A')}: "
                        try:
                            reported_eps = float(earning.get('reportedEPS', 0))
                            estimated_eps = float(earning.get('estimatedEPS', 0))
                            surprise_pct = float(earning.get('surprisePercentage', 0))
                            
                            result_text += f"Reported EPS ${reported_eps:.2f}, "
                            result_text += f"Estimated EPS ${estimated_eps:.2f}, "
                            result_text += f"Surprise {surprise_pct:+.2f}%\n"
                        except:
                            result_text += f"Reported {earning.get('reportedEPS', 'N/A')}, "
                            result_text += f"Estimated {earning.get('estimatedEPS', 'N/A')}\n"
            
            # Default handling for other function types
            else:
                result_text += json.dumps(data, indent=2) + "\n"
                
        except Exception as e:
            result_text += f"Error retrieving {data_point['function']}: {str(e)}\n"
    
    # Calculate and add financial ratios section
    result_text += f"\nFINANCIAL RATIOS\n{'-' * 30}\n"
    
    try:
        # Get necessary data for calculations
        overview = all_data.get("OVERVIEW", {})
        income_statement = all_data.get("INCOME_STATEMENT", {})
        balance_sheet = all_data.get("BALANCE_SHEET", {})
        cash_flow = all_data.get("CASH_FLOW", {})
        quote = all_data.get("GLOBAL_QUOTE", {}).get("Global Quote", {})
        
        # Valuation Ratios
        result_text += "Valuation Ratios:\n"
        
        # P/E Ratio (Price to Earnings)
        if "PERatio" in overview:
            try:
                pe_ratio = float(overview["PERatio"])
                result_text += f"P/E Ratio: {pe_ratio:.2f}\n"
            except:
                result_text += f"P/E Ratio: {overview.get('PERatio', 'N/A')}\n"
        
        # PEG Ratio (Price/Earnings to Growth)
        if "PEGRatio" in overview:
            try:
                peg_ratio = float(overview["PEGRatio"])
                result_text += f"PEG Ratio: {peg_ratio:.2f}\n"
            except:
                result_text += f"PEG Ratio: {overview.get('PEGRatio', 'N/A')}\n"
        
        # P/B Ratio (Price to Book)
        try:
            market_cap = float(overview.get("MarketCapitalization", 0))
            book_value = float(overview.get("BookValue", 0)) * float(overview.get("SharesOutstanding", 0))
            if market_cap > 0 and book_value > 0:
                pb_ratio = market_cap / book_value
                result_text += f"P/B Ratio: {pb_ratio:.2f}\n"
        except:
            # If we can't calculate it, use the overview data if available
            if "PriceToBookRatio" in overview:
                result_text += f"P/B Ratio: {overview['PriceToBookRatio']}\n"
        
        # Calculate P/S (Price to Sales) Ratio
        try:
            market_cap = float(overview.get("MarketCapitalization", 0))
            revenue = 0
            if income_statement and "annualReports" in income_statement and income_statement["annualReports"]:
                revenue = float(income_statement["annualReports"][0].get("totalRevenue", 0))
            
            if market_cap > 0 and revenue > 0:
                ps_ratio = market_cap / revenue
                result_text += f"P/S Ratio: {ps_ratio:.2f}\n"
        except:
            # If we can't calculate it, use the overview data if available
            if "PriceToSalesRatioTTM" in overview:
                result_text += f"P/S Ratio: {overview['PriceToSalesRatioTTM']}\n"
        
        # Dividend Yield
        if "DividendYield" in overview:
            try:
                dividend_yield = float(overview["DividendYield"]) * 100
                result_text += f"Dividend Yield: {dividend_yield:.2f}%\n"
            except:
                result_text += f"Dividend Yield: {overview.get('DividendYield', 'N/A')}\n"
        
        # Profitability Ratios
        result_text += "\nProfitability Ratios:\n"
        
        # ROE (Return on Equity)
        if "ReturnOnEquityTTM" in overview:
            try:
                roe = float(overview["ReturnOnEquityTTM"]) * 100
                result_text += f"Return on Equity (ROE): {roe:.2f}%\n"
            except:
                result_text += f"Return on Equity (ROE): {overview.get('ReturnOnEquityTTM', 'N/A')}\n"
        else:
            # Calculate ROE manually
            try:
                if income_statement and balance_sheet and "annualReports" in income_statement and "annualReports" in balance_sheet:
                    net_income = float(income_statement["annualReports"][0].get("netIncome", 0))
                    equity = float(balance_sheet["annualReports"][0].get("totalShareholderEquity", 0))
                    if equity > 0:
                        roe = (net_income / equity) * 100
                        result_text += f"Return on Equity (ROE): {roe:.2f}%\n"
            except:
                pass
        
        # ROA (Return on Assets)
        if "ReturnOnAssetsTTM" in overview:
            try:
                roa = float(overview["ReturnOnAssetsTTM"]) * 100
                result_text += f"Return on Assets (ROA): {roa:.2f}%\n"
            except:
                result_text += f"Return on Assets (ROA): {overview.get('ReturnOnAssetsTTM', 'N/A')}\n"
        else:
            # Calculate ROA manually
            try:
                if income_statement and balance_sheet and "annualReports" in income_statement and "annualReports" in balance_sheet:
                    net_income = float(income_statement["annualReports"][0].get("netIncome", 0))
                    assets = float(balance_sheet["annualReports"][0].get("totalAssets", 0))
                    if assets > 0:
                        roa = (net_income / assets) * 100
                        result_text += f"Return on Assets (ROA): {roa:.2f}%\n"
            except:
                pass
        
        # Profit Margin
        if "ProfitMargin" in overview:
            try:
                profit_margin = float(overview["ProfitMargin"]) * 100
                result_text += f"Profit Margin: {profit_margin:.2f}%\n"
            except:
                result_text += f"Profit Margin: {overview.get('ProfitMargin', 'N/A')}\n"
        
        # Operating Margin
        if "OperatingMarginTTM" in overview:
            try:
                operating_margin = float(overview["OperatingMarginTTM"]) * 100
                result_text += f"Operating Margin: {operating_margin:.2f}%\n"
            except:
                result_text += f"Operating Margin: {overview.get('OperatingMarginTTM', 'N/A')}\n"
        
        # Liquidity & Solvency Ratios
        result_text += "\nLiquidity & Solvency Ratios:\n"
        
        # Current Ratio
        try:
            if balance_sheet and "annualReports" in balance_sheet and balance_sheet["annualReports"]:
                current_assets = float(balance_sheet["annualReports"][0].get("totalCurrentAssets", 0))
                current_liabilities = float(balance_sheet["annualReports"][0].get("totalCurrentLiabilities", 0))
                if current_liabilities > 0:
                    current_ratio = current_assets / current_liabilities
                    result_text += f"Current Ratio: {current_ratio:.2f}\n"
        except:
            pass
        
        # Quick Ratio (Acid-Test Ratio)
        try:
            if balance_sheet and "annualReports" in balance_sheet and balance_sheet["annualReports"]:
                current_assets = float(balance_sheet["annualReports"][0].get("totalCurrentAssets", 0))
                inventory = float(balance_sheet["annualReports"][0].get("inventory", 0))
                current_liabilities = float(balance_sheet["annualReports"][0].get("totalCurrentLiabilities", 0))
                if current_liabilities > 0:
                    quick_ratio = (current_assets - inventory) / current_liabilities
                    result_text += f"Quick Ratio: {quick_ratio:.2f}\n"
        except:
            pass
        
        # Debt-to-Equity Ratio
        try:
            if balance_sheet and "annualReports" in balance_sheet and balance_sheet["annualReports"]:
                total_debt = float(balance_sheet["annualReports"][0].get("shortLongTermDebtTotal", 0))
                equity = float(balance_sheet["annualReports"][0].get("totalShareholderEquity", 0))
                if equity > 0:
                    debt_equity_ratio = total_debt / equity
                    result_text += f"Debt-to-Equity Ratio: {debt_equity_ratio:.2f}\n"
        except:
            pass
        
        # Debt Ratio (Total Debt / Total Assets)
        try:
            if balance_sheet and "annualReports" in balance_sheet and balance_sheet["annualReports"]:
                total_debt = float(balance_sheet["annualReports"][0].get("shortLongTermDebtTotal", 0))
                total_assets = float(balance_sheet["annualReports"][0].get("totalAssets", 0))
                if total_assets > 0:
                    debt_ratio = total_debt / total_assets
                    result_text += f"Debt Ratio: {debt_ratio:.2f}\n"
        except:
            pass
        
        # Efficiency/Activity Ratios
        result_text += "\nEfficiency Ratios:\n"
        
        # Asset Turnover
        try:
            if income_statement and balance_sheet and "annualReports" in income_statement and "annualReports" in balance_sheet:
                revenue = float(income_statement["annualReports"][0].get("totalRevenue", 0))
                assets = float(balance_sheet["annualReports"][0].get("totalAssets", 0))
                if assets > 0:
                    asset_turnover = revenue / assets
                    result_text += f"Asset Turnover: {asset_turnover:.2f}\n"
        except:
            pass
        
        # Inventory Turnover
        try:
            if income_statement and balance_sheet and "annualReports" in income_statement and "annualReports" in balance_sheet:
                cogs = float(income_statement["annualReports"][0].get("costofGoodsAndServicesSold", 0))
                inventory = float(balance_sheet["annualReports"][0].get("inventory", 0))
                if inventory > 0:
                    inventory_turnover = cogs / inventory
                    result_text += f"Inventory Turnover: {inventory_turnover:.2f}\n"
        except:
            pass
    
    except Exception as e:
        result_text += f"Error calculating financial ratios: {str(e)}\n"
    
    # Add an analysis summary at the end
    result_text += f"\n{'=' * 50}\n"
    result_text += f"ANALYSIS SUMMARY FOR {symbol}\n"
    result_text += f"{'=' * 50}\n"
    result_text += "Generated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n"
    
    return result_text

company_analyzer_tool = Tool(
    name = "company_analyzer",
    func=analyze_company,
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
)

# Example usage
if __name__ == "__main__":

    analysis = analyze_company("AAPL")
    print(analysis)
    