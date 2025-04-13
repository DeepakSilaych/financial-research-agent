from openai import OpenAI
from dotenv import load_dotenv
import os
from src.prompts import SAFETY_CHECKER_PROMPT
from src.logger import info, warning, error
from datetime import datetime
import src.flow as flow
import json
import re
from src.visualization_extractor import extract_visualizations

# Load environment variables from .env file
load_dotenv()

client = OpenAI(
    api_key= os.environ.get("OPENAI_API_KEY")
)

def check_query_safety(user_input, user_id="anonymous"):
    """Check if a query is safe and refine it if needed"""
    info(f"Checking safety for query: '{user_input}'")
    
    try:
        response = client.responses.create(
            model="gpt-4-turbo",
            instructions=SAFETY_CHECKER_PROMPT,
            input= user_input
        )

        refined_text = response.output[0].content[0].text.strip()

        # Check if harmful (empty output = harmful)
        if not refined_text:
            warning(f"Unsafe query detected: '{user_input}'")
            return {
                "is_safe": False,
                "refined_query": None
            }
        else:
            if refined_text != user_input:
                info(f"Query refined from '{user_input}' to '{refined_text}'")
            else:
                info("Query passed safety check without refinement")
                
            return {
                "is_safe": True,
                "refined_query": refined_text
            }
    except Exception as e:
        error(f"Error in safety check: {str(e)}")
        # Return original query on error, assuming it's safe
        return {
            "is_safe": True,
            "refined_query": user_input
        }

def process_query(user_input, user_id=None, visualization_options=None):
    """Process a user query through the complete workflow"""
    # Generate a unique session ID if not provided
    if not user_id:
        user_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    info(f"Processing query for session {user_id}: '{user_input}'")
    
    # Process visualization options
    if visualization_options is None:
        visualization_options = {
            "include_tables": True,
            "include_graphs": True,
            "max_tables": 5,
            "max_graphs": 3
        }
    
    # 1. Check if query is safe
    safety_result = check_query_safety(user_input, user_id)
    
    if not safety_result["is_safe"]:
        warning(f"Query rejected: {user_input}")
        return {
            "status": "rejected",
            "reason": "Query contains harmful content",
            "response": None,
            "graphs": [],
            "tables": []
        }
    
    # 2. Process through agent workflow using the original query directly
    agent_response = flow.run_agent_loop(
        flow.agent, 
        query=user_input,
        original_query=user_input,
        metadata={},
        max_retries=5, 
        user_id=user_id
    )
    
    # If we have the complete dict response with visualization data, use it
    if isinstance(agent_response, dict):
        result = {
            "status": "success",
            "query": user_input,
            "response": agent_response.get("response", ""),
            "metadata": agent_response.get("metadata", {}),
            "graphs": agent_response.get("graphs", []),
            "tables": agent_response.get("tables", [])
        }
    else:
        # For backwards compatibility when agent_response is just a string
        result = {
            "status": "success",
            "query": user_input,
            "response": agent_response if isinstance(agent_response, str) else str(agent_response),
            "metadata": {},
            "graphs": [],
            "tables": []
        }
    
    # Extract tables and graphs if needed
    include_tables = visualization_options.get("include_tables", True)
    include_graphs = visualization_options.get("include_graphs", True)
    max_tables = visualization_options.get("max_tables", 5)
    max_graphs = visualization_options.get("max_graphs", 3)
    
    if (include_tables or include_graphs) and (not result["graphs"] or not result["tables"]):
        try:
            info(f"Extracting visualizations for query: '{user_input[:100]}...'")
            visualizations = extract_visualizations(
                result["response"], 
                user_input,
                max_tables=max_tables,
                max_graphs=max_graphs
            )
            
            if include_tables and not result["tables"]:
                result["tables"] = visualizations.get("tables", [])
                
            if include_graphs and not result["graphs"]:
                result["graphs"] = visualizations.get("graphs", [])
        except Exception as e:
            error(f"Error extracting visualizations: {e}")
    
    return result

# Example usage
if __name__ == "__main__":
    query = "What are the major trends in the semiconductor industry in 2023? Focus on NVIDIA, AMD, and Intel."
    result = process_query(query)

    info("=================================Result ==================================")
    info(result)
    info("==========================================================================")