from dotenv import load_dotenv
import os
import json
import flow

load_dotenv()

def main():
    user_input = "What were Tesla's EBITDA margins in 2023 compared to other EV manufacturers? use web scrap"
    
    result = flow.process_user_query(user_input)
    
    if result["status"] == "success":
        print("\n=== Query Processing Results ===")
        print(f"Refined Query: {result['refined_query']}")
        print(f"Extracted Metadata: {json.dumps(result['metadata'], indent=2)}")
        print(f"Tool Selection: {json.dumps(result['tool_selection'], indent=2)}")
        print("\n=== Response ===")
        print(result["response"])
    else:
        print(f"Error: {result['message']}")

if __name__ == "__main__":
    main() 