from openai import OpenAI
from dotenv import load_dotenv
import os
from prompts import SAFETY_CHECKER_PROMPT, METADATA_EXTRACTION_PROMPT
from logger import info, warning, error
from datetime import datetime
import flow

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
    """Extract metadata from a user query"""
    info(f"Extracting metadata for query: '{user_query}'")
    
    try:
        response = client.responses.create(
            model="gpt-4-turbo",
            instructions=METADATA_EXTRACTION_PROMPT,
            input= user_query
        )

        output = response.output[0].content[0].text
        info(f"Extracted metadata: {output}")
        return output
    except Exception as e:
        error(f"Error extracting metadata: {str(e)}")
        return "{}"

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
    refined_query = safety_result["refined_query"]
    metadata = validate_and_extract_metadata(refined_query, user_id)
    
    # 3. Process through agent workflow
    agent_response = flow.run_agent_loop(flow.agent, refined_query, max_retries=3, user_id=user_id)
    
    return {
        "status": "success",
        "metadata": metadata,
        "response": agent_response
    }

# Example usage
if __name__ == "__main__":
    user_input = "What is the stock price of Apple?"
    result = process_query(user_input)
    
    if result["status"] == "success":
        print("\nResult:")
        print(result["response"])
    else:
        print(f"\nQuery rejected: {result['reason']}")
   

