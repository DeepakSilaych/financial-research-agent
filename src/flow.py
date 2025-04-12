import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from tools.stock_info_tool import stock_tool
from tools.news_tool import news_tool 
from tools.company_analyzer_tool import company_analyzer_tool
from tools.fred_market_tool import fred_tool
from tools.stock_info_tool import financial_statements_tool
from tools.stock_info_tool import historical_performance_tool
from tools.stock_info_tool import technical_indicators_tool 
from tools.company_profile_tool import company_profile_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from prompts import MISSING_INFO_CHECKER_PROMPT, RESPONSE_MERGER_PROMPT
from logger import info, error, log_request, log_response
import uuid
import json

# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Set up LangChain agent
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools=[stock_tool, news_tool, company_analyzer_tool, fred_tool,company_profile_tool,financial_statements_tool,historical_performance_tool,technical_indicators_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# GPT-4 for advanced processing
gpt4_llm = ChatOpenAI(model="gpt-4", temperature=0)
parser = StrOutputParser()

def check_missing_parts(original_query: str, expanded_query: str, agent_response: str, answered_parts: list = None, qa_pairs: list = None) -> list[str]:
    """
    Check if parts of the queries were not answered in the response
    
    Args:
        original_query: The user's original query
        expanded_query: The expanded research query with detailed questions
        agent_response: The agent's response to analyze
        answered_parts: List of parts that have already been answered in previous iterations
        qa_pairs: Previous question-answer pairs for context
        
    Returns:
        List of specific questions for parts that remain unanswered
    """
    info(f"Checking for missing parts in response...")
    
    # Format Q&A pairs for the prompt if available
    qa_pairs_text = ""
    if qa_pairs and len(qa_pairs) > 0:
        qa_pairs_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs])
    
    # Add context about already answered parts if available
    system_prompt = MISSING_INFO_CHECKER_PROMPT
    if answered_parts and len(answered_parts) > 0:
        answered_str = "\n".join([f"- {part}" for part in answered_parts])
        system_prompt += f"\n\nThe following parts have already been answered in previous responses, so don't include these:\n{answered_str}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt)
    ])
    chain = prompt | gpt4_llm | parser
    
    try:
        missing_info = chain.invoke({
            "original_query": original_query,
            "expanded_query": expanded_query,
            "qa_pairs": qa_pairs_text,
            "agent_response": agent_response
        })

        if "none" in missing_info.lower():
            info("No missing parts detected")
            return []
            
        missing_parts = [line.strip("- ").strip() for line in missing_info.split("\n") if line.strip()]
        info(f"Detected {len(missing_parts)} missing parts")
        return missing_parts
    except Exception as e:
        error(f"Error checking for missing parts: {str(e)}")
        return []

def merge_responses(original_query: str, expanded_query: str, qa_pairs: list, metadata: dict) -> str:
    """
    Merge multiple question-answer pairs into a cohesive response
    
    Args:
        original_query: The user's original query
        expanded_query: The expanded research query
        qa_pairs: List of question-answer pairs from agent runs
        metadata: Metadata about the query
        
    Returns:
        A cohesive, structured response addressing all aspects of the query
    """
    info(f"Merging {len(qa_pairs)} responses into final output")
    
    # Format the QA pairs for the prompt
    qa_text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in qa_pairs])
    
    # Convert metadata to a formatted string
    metadata_str = json.dumps(metadata, indent=2) if metadata else "{}"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", RESPONSE_MERGER_PROMPT)
    ])
    chain = prompt | gpt4_llm | parser
    
    try:
        merged_response = chain.invoke({
            "original_query": original_query,
            "expanded_query": expanded_query,
            "qa_pairs": qa_text,
            "metadata": metadata_str
        })
        
        info(f"Generated merged response of length: {len(merged_response)}")
        return merged_response
    except Exception as e:
        error(f"Error merging responses: {str(e)}")
        # Fallback to just returning the concatenated responses
        return f"Original Query: {original_query}\n\n" + qa_text

def run_agent_loop(agent, query, original_query=None, metadata=None, max_retries=5, user_id=None):
    """
    Run the agent with retry loop for handling missing information
    
    Args:
        agent: The LangChain agent to use
        query: The expanded query to process
        original_query: The user's original query (if different from expanded)
        metadata: Metadata about the query content
        max_retries: Maximum number of iterations to perform
        user_id: User identifier for tracking
        
    Returns:
        A cohesive response addressing all aspects of the query
    """
    # Use the query as original_query if not provided
    if original_query is None:
        original_query = query
        
    # Generate a session ID if not provided
    if not user_id:
        user_id = f"session_{uuid.uuid4().hex[:8]}"
        
    info(f"Starting agent loop for user {user_id}")
    info(f"Original query: '{original_query}'")
    info(f"Expanded query: '{query}'")
    log_request(user_id, original_query)
    
    seen_queries = set([query])  # Track queries we've already processed
    to_ask = [query]  # Queue of queries to process
    answered_parts = []  # Track parts that have been answered
    qa_pairs = []  # Store Q&A pairs for final merging
    iteration_count = 0
    
    for iteration in range(max_retries):
        iteration_count = iteration + 1
        if not to_ask:
            info("No more questions to ask, ending agent loop")
            break

        current_query = to_ask.pop(0)
        info(f"Iteration {iteration_count}: Asking agent: '{current_query}'")
        
        try:
            # Invoke the agent with the current query
            result = agent.invoke(current_query)
            response = result["output"] if isinstance(result, dict) else str(result)
            info(f"Agent response ({len(response)} chars): {response[:100]}...")
            
            # Store this Q&A pair
            qa_pairs.append((current_query, response))
            
            # Pass the accumulated qa_pairs to the missing parts checker for context
            missing = check_missing_parts(
                original_query=original_query, 
                expanded_query=query, 
                agent_response=response, 
                answered_parts=answered_parts, 
                qa_pairs=qa_pairs
            )
            
            # Consider this part answered even if some details are missing
            answered_parts.append(current_query)
            
            # Add missing parts to the queue if they're new
            for part in missing:
                if part not in seen_queries:
                    info(f"Adding follow-up question: '{part}'")
                    to_ask.append(part)
                    seen_queries.add(part)
                    
        except Exception as e:
            error(f"Error in agent iteration {iteration_count}: {str(e)}")
            # Store the error as the response
            qa_pairs.append((current_query, f"Error processing your request. {str(e)}"))

    info(f"Agent loop completed after {iteration_count} iterations with {len(qa_pairs)} Q&A pairs")
    
    # Merge all responses into a cohesive answer
    final_response = merge_responses(original_query, query, qa_pairs, metadata)
    
    log_response(user_id, original_query, final_response)
    return final_response

if __name__ == "__main__":
    # Example usage
    query = "Give me a detailed company profile of Tesla, including its industry, business model, key products/services, market position, leadership, and recent news."
    expanded_query = """
    - What are the primary sectors of Tesla's operation? How does Tesla's business model integrate these sectors?
    - Detail Tesla's major products and their contribution to revenue.
    - Evaluate Tesla's current market position in the electric vehicle and renewable energy sectors globally.
    - Review the current leadership team of Tesla, focusing on key figures like Elon Musk.
    - What are the most recent developments and news about Tesla that could impact its business?
    - Who are Tesla's primary competitors in both the electric vehicle and renewable energy sectors?
    """
    
    metadata = {
        "company_entities": [
            {
                "name": "Tesla",
                "type": "established_company",
                "description": "Leading manufacturer of electric vehicles and clean energy solutions",
                "stage": "public",
                "founding_year": "2003"
            }
        ],
        "industry": "Automotive and Energy",
        "sub_industry": "Electric Vehicles and Clean Energy",
        "country": "USA",
        "region": "North America"
    }
    
    user_id = "user_1234"  # Example user ID
    response = run_agent_loop(agent, expanded_query, original_query=query, metadata=metadata, user_id=user_id)
    print(response)
