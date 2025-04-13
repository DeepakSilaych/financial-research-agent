from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from src.prompts import TABLE_AND_GRAPH_EXTRACTION_PROMPT
from src.logger import info, warning, error

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY")
)

def extract_visualizations(response_text, query, max_tables=5, max_graphs=3):
    """
    Extract tables and graphs from a text response.
    
    Args:
        response_text (str): The text response to extract visualizations from.
        query (str): The original query that generated the response.
        max_tables (int): Maximum number of tables to extract.
        max_graphs (int): Maximum number of graphs to extract.
        
    Returns:
        dict: Dictionary containing tables and graphs.
    """
    try:
        info(f"Extracting visualizations for query: {query[:100]}...")
        
        # Format the prompt with the response and query
        prompt = TABLE_AND_GRAPH_EXTRACTION_PROMPT.format(
            response=response_text,
            query=query
        )
        
        # Query the OpenAI API
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a financial data visualization specialist."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        # Extract the content
        content = response.choices[0].message.content
        
        # Parse the JSON response
        try:
            visualization_data = json.loads(content)
            
            # Validate the structure
            if not isinstance(visualization_data, dict):
                warning("Visualization data is not a dictionary")
                return {"tables": [], "graphs": []}
            
            # Extract tables and graphs
            tables = visualization_data.get("tables", [])
            graphs = visualization_data.get("graphs", [])
            
            # Limit the number of tables and graphs
            tables = tables[:max_tables]
            graphs = graphs[:max_graphs]
            
            info(f"Extracted {len(tables)} tables and {len(graphs)} graphs")
            
            return {
                "tables": tables,
                "graphs": graphs
            }
        except json.JSONDecodeError as e:
            error(f"Failed to parse visualization data: {e}")
            return {"tables": [], "graphs": []}
            
    except Exception as e:
        error(f"Error extracting visualizations: {e}")
        return {"tables": [], "graphs": []}

# Example usage
if __name__ == "__main__":
    response_text = """
    Apple Inc. (AAPL) Financial Overview:
    
    Key Metrics (Q3 2023):
    - Revenue: $81.8 billion
    - EPS: $1.26
    - Operating Margin: 29.2%
    - Net Profit: $19.9 billion
    
    Historical Stock Performance:
    - 2020: +82.3%
    - 2021: +34.7%
    - 2022: -26.8%
    - 2023 YTD: +48.2%
    
    Product Revenue Breakdown:
    - iPhone: $39.7 billion (48.5%)
    - Services: $21.2 billion (25.9%)
    - Mac: $6.8 billion (8.3%)
    - iPad: $5.8 billion (7.1%)
    - Wearables & Home: $8.3 billion (10.2%)
    """
    
    query = "Give me a financial overview of Apple Inc. with key metrics and historical performance"
    
    visualizations = extract_visualizations(response_text, query)
    print(json.dumps(visualizations, indent=2)) 