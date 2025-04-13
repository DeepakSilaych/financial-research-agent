import os
import pandas as pd
from dotenv import load_dotenv
from langchain.agents import Tool
from src.logger import info, error, warning, get_logger

# Setup logger for the module
logger = get_logger("startup_data_tool")

# Load .env file
load_dotenv()

# Path to the CSV file
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Growjo-1k-list.csv")

def search_startups(query: str) -> str:
    """Search for startup information based on a query (company name, industry, etc)."""
    info(f"Searching startups with query: {query}")
    
    try:
        # Load the CSV data
        df = pd.read_csv(CSV_PATH)
        
        # Clean query
        query = query.strip().lower()
        
        # First try to find exact company match
        company_matches = df[df['company_name'].str.lower() == query]
        
        # If no exact match, try to find companies that contain the query
        if company_matches.empty:
            company_matches = df[df['company_name'].str.lower().str.contains(query)]
            
        # If still no match, try to find by industry
        if company_matches.empty:
            company_matches = df[df['Industry'].str.lower() == query]
            
        # If still no match, try to find industry containing query
        if company_matches.empty:
            company_matches = df[df['Industry'].str.lower().str.contains(query)]
        
        # If we have matches, format and return them
        if not company_matches.empty:
            # Sort by GrowjoRanking
            company_matches = company_matches.sort_values(by='GrowjoRanking')
            
            # Limit to top 5 results
            top_results = company_matches.head(5)
            
            result = f"Found {len(top_results)} startups related to '{query}':\n\n"
            
            for _, company in top_results.iterrows():
                result += f"📊 {company['company_name']} ({company.get('url', 'N/A')})\n"
                result += f"   Location: {company.get('city', 'N/A')}, {company.get('state', 'N/A')}, {company.get('country', 'N/A')}\n"
                result += f"   Industry: {company.get('Industry', 'N/A')}\n"
                result += f"   Employees: {company.get('employees', 'N/A')}\n"
                
                # Add funding information if available
                valuation = company.get('valuation', 'N/A')
                funding = company.get('total_funding', 'N/A')
                
                if valuation != 'N/A' and valuation:
                    result += f"   Valuation: {valuation}\n"
                
                if funding != 'N/A' and funding:
                    result += f"   Total Funding: {funding}\n"
                
                # Add growth information if available
                growth = company.get('growth_percentage', 'N/A')
                if growth != 'N/A' and growth:
                    result += f"   Growth: {growth}\n"
                
                # Add founding year if available
                founded = company.get('founded', 'N/A')
                if founded != 'N/A' and founded and not pd.isna(founded):
                    result += f"   Founded: {founded}\n"
                
                # Add investors if available
                investors = company.get('LeadInvestors', 'N/A')
                if investors != 'N/A' and investors and not pd.isna(investors):
                    result += f"   Lead Investors: {investors}\n"
                
                result += "\n"
            
            return result
        else:
            return f"No startups found related to '{query}'. Try searching for a different company name or industry."
    
    except Exception as e:
        error_msg = f"Error searching startups: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_top_startups(count: int = 10) -> str:
    """Get the top N startups by ranking."""
    info(f"Getting top {count} startups")
    
    try:
        # Load the CSV data
        df = pd.read_csv(CSV_PATH)
        
        # Sort by GrowjoRanking and take top N
        top_startups = df.sort_values(by='GrowjoRanking').head(count)
        
        result = f"🔥 Top {count} Fastest Growing Startups:\n\n"
        
        for _, company in top_startups.iterrows():
            result += f"#{company['GrowjoRanking']} {company['company_name']} ({company.get('url', 'N/A')})\n"
            result += f"   Industry: {company.get('Industry', 'N/A')}\n"
            result += f"   Location: {company.get('city', 'N/A')}, {company.get('country', 'N/A')}\n"
            
            # Add funding information if available
            valuation = company.get('valuation', 'N/A')
            funding = company.get('total_funding', 'N/A')
            
            if valuation != 'N/A' and valuation:
                result += f"   Valuation: {valuation}\n"
            
            if funding != 'N/A' and funding:
                result += f"   Total Funding: {funding}\n"
            
            # Add growth if available
            growth = company.get('growth_percentage', 'N/A')
            if growth != 'N/A' and growth:
                result += f"   Growth: {growth}\n"
            
            result += "\n"
        
        return result
    
    except Exception as e:
        error_msg = f"Error getting top startups: {str(e)}"
        logger.error(error_msg)
        return error_msg

def get_startups_by_industry(industry: str) -> str:
    """Get startups in a specific industry."""
    info(f"Getting startups in industry: {industry}")
    
    try:
        # Load the CSV data
        df = pd.read_csv(CSV_PATH)
        
        # Clean input
        industry = industry.strip().lower()
        
        # Find companies in the specified industry
        industry_matches = df[df['Industry'].str.lower() == industry]
        
        # If no exact match, try to find industry containing query
        if industry_matches.empty:
            industry_matches = df[df['Industry'].str.lower().str.contains(industry)]
        
        # If we have matches, format and return them
        if not industry_matches.empty:
            # Sort by GrowjoRanking
            industry_matches = industry_matches.sort_values(by='GrowjoRanking')
            
            # Limit to top 10 results
            top_results = industry_matches.head(10)
            
            result = f"Found {len(top_results)} top startups in the '{industry}' industry:\n\n"
            
            for _, company in top_results.iterrows():
                result += f"📊 {company['company_name']} ({company.get('url', 'N/A')})\n"
                result += f"   Location: {company.get('city', 'N/A')}, {company.get('state', 'N/A')}, {company.get('country', 'N/A')}\n"
                
                # Add funding information if available
                valuation = company.get('valuation', 'N/A')
                funding = company.get('total_funding', 'N/A')
                
                if valuation != 'N/A' and valuation:
                    result += f"   Valuation: {valuation}\n"
                
                if funding != 'N/A' and funding:
                    result += f"   Total Funding: {funding}\n"
                
                # Add growth if available
                growth = company.get('growth_percentage', 'N/A')
                if growth != 'N/A' and growth:
                    result += f"   Growth: {growth}\n"
                
                result += "\n"
            
            return result
        else:
            return f"No startups found in the '{industry}' industry. Try searching for a different industry."
    
    except Exception as e:
        error_msg = f"Error getting startups by industry: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Create LangChain tools
startup_search_tool = Tool(
    name="Startup Search",
    func=search_startups,
    description="Search for startup information by company name or industry. Input should be a company name or industry like 'Anthropic', 'AI', 'Fintech', etc."
)

top_startups_tool = Tool(
    name="Top Startups",
    func=get_top_startups,
    description="Get a list of the top fastest-growing startups. Input should be the number of startups to show (default 10)."
)

industry_startups_tool = Tool(
    name="Industry Startups",
    func=get_startups_by_industry,
    description="Get a list of top startups in a specific industry. Input should be an industry name like 'AI', 'Fintech', etc."
)

# Main tool that combines the search capabilities
STARTUP_TOOL_DESCRIPTION = """**Use this tool when the user asks about startups, high-growth companies, unicorns, or venture-backed businesses.** 
This tool provides information on the fastest growing startups worldwide, including funding, valuation, and industry data.
Use this tool to answer questions about specific startups, industries with promising startups, or general startup landscape.
Input should be a search query like 'Anthropic', 'AI startups', 'top fintech companies', etc."""

# Create a combined tool that routes to the appropriate function
def startup_tool_router(query: str) -> str:
    """Router for startup-related queries to determine which function to call."""
    query = query.strip().lower()
    
    # Check if it's asking for top startups
    if "top" in query and ("startup" in query or "companies" in query or "business" in query):
        # Extract number if specified
        import re
        count_match = re.search(r'top\s+(\d+)', query)
        count = int(count_match.group(1)) if count_match else 10
        
        # Cap at 20 to avoid overly long responses
        count = min(count, 20)
        
        return get_top_startups(count)
    
    # Check if it's asking for startups in a specific industry
    elif "industry" in query or "sector" in query:
        # Extract the industry
        parts = query.split("in")
        if len(parts) > 1:
            industry = parts[1].strip()
            return get_startups_by_industry(industry)
    
    # Default to search
    return search_startups(query)

# The main tool to be exported
startup_tool = Tool(
    name="Startup Information Tool",
    func=startup_tool_router,
    description=STARTUP_TOOL_DESCRIPTION
) 