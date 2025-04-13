from openai import OpenAI
from dotenv import load_dotenv
import os
from prompts import SAFETY_CHECKER_PROMPT, METADATA_AND_QUERY_ENRICHMENT_PROMPT
from logger import info, warning, error
from datetime import datetime
import flow
import json
import re

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

def validate_and_extract_metadata(user_query, user_id="anonymous"):
    """
    Extract metadata from a user query
    
    Returns:
        dict: A dictionary containing:
            - metadata: JSON metadata as a Python dict
            - expanded_query: Markdown expanded query as a string
    """
    info(f"Extracting metadata for query: '{user_query}'")
    
    try:
        response = client.responses.create(
            model="gpt-4-turbo",
            instructions=METADATA_AND_QUERY_ENRICHMENT_PROMPT,
            input= user_query
        )

        output = response.output[0].content[0].text
        info(f"Raw extracted output: {output}")
        
        # Extract JSON part (from PART 1: METADATA EXTRACTION)
        json_match = re.search(r'```json\s*(.*?)\s*```', output, re.DOTALL)
        metadata = {}
        if json_match:
            try:
                metadata = json.loads(json_match.group(1))
                info(f"Parsed metadata: {metadata}")
            except json.JSONDecodeError as e:
                error(f"Error parsing JSON metadata: {str(e)}")
        
        # Extract the expanded query (from PART 2: QUERY EXPANSION)
        expanded_query = ""
        if "PART 2: QUERY EXPANSION" in output:
            expanded_query = output.split("PART 2: QUERY EXPANSION", 1)[1].strip()
            info(f"Extracted expanded query of length: {len(expanded_query)}")
        
        return {
            "metadata": metadata,
            "expanded_query": expanded_query
        }
    except Exception as e:
        error(f"Error extracting metadata: {str(e)}")
        return {
            "metadata": {},
            "expanded_query": ""
        }

def process_query(user_input, user_id=None):
    """Process a user query through the complete workflow"""
    # Generate a unique session ID if not provided
    if not user_id:
        user_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    info(f"Processing query for session {user_id}: '{user_input}'")
    
    # 1. Check if query is safe
    safety_result = check_query_safety(user_input, user_id)
    
    if not safety_result["is_safe"]:
        warning(f"Query rejected: {user_input}")
        return {
            "status": "rejected",
            "reason": "Query contains harmful content",
            "response": None
        }
    
    # 2. Extract metadata
    metadata_result = validate_and_extract_metadata(user_input, user_id)
    
    # Use the expanded query if available, otherwise use the refined query
    query_for_agent = metadata_result["expanded_query"] if metadata_result["expanded_query"] else user_input
    info(f"Using query for agent: '{query_for_agent[:100]}...'")
    
    # 3. Process through enhanced agent workflow with the improved arguments
    agent_response = flow.run_agent_loop(
        flow.agent, 
        query=query_for_agent,
        original_query=user_input,
        metadata=metadata_result["metadata"],
        max_retries=5, 
        user_id=user_id
    )
    
    return {
        "status": "success",
        "metadata": metadata_result["metadata"],
        "expanded_query": query_for_agent,
        "response": agent_response
    }

# Example usage
if __name__ == "__main__":
    query = "Give me matrix for tesla stocks"
    result = process_query(query)


    info("=================================Result ==================================")
    info(result["response"])
    info("==========================================================================")