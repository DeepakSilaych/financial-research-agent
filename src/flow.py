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
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Set up LangChain agent
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools=[stock_tool, news_tool, company_analyzer_tool, fred_tool, company_profile_tool, financial_statements_tool, historical_performance_tool, technical_indicators_tool],
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

def process_query(agent, query: str) -> tuple:
    """Process a single query through the agent and return the question-answer pair"""
    try:
        info(f"Processing query: '{query}'")
        result = agent.invoke(query)
        response = result["output"] if isinstance(result, dict) else str(result)
        info(f"Got response ({len(response)} chars): {response[:100]}...")
        return (query, response)
    except Exception as e:
        error(f"Error processing query: {str(e)}")
        return (query, f"Error processing your request. {str(e)}")

def process_queries_in_parallel(agent, queries: list, max_workers: int = 4) -> list:
    """Process multiple queries in parallel using a thread pool"""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_query = {executor.submit(process_query, agent, query): query for query in queries}
        
        # Process results as they complete
        for future in future_to_query:
            try:
                results.append(future.result())
            except Exception as e:
                query = future_to_query[future]
                error(f"Error in parallel processing for query '{query}': {str(e)}")
                results.append((query, f"Error processing your request. {str(e)}"))
    
    return results

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

def run_agent_loop(agent, query, original_query=None, metadata=None, max_retries=5, user_id=None, max_parallel_workers=3):
    """
    Run the agent with retry loop for handling missing information
    
    Args:
        agent: The LangChain agent to use
        query: The expanded query to process
        original_query: The user's original query (if different from expanded)
        metadata: Metadata about the query content
        max_retries: Maximum number of iterations to perform
        user_id: User identifier for tracking
        max_parallel_workers: Maximum number of parallel workers for decomposed questions
        
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
    answered_parts = []  # Track parts that have been answered
    qa_pairs = []  # Store Q&A pairs for final merging
    
    # First iteration - process the main query
    info(f"Iteration 1: Processing main query")
    main_qa_pair = process_query(agent, query)
    qa_pairs.append(main_qa_pair)
    answered_parts.append(query)
    
    # Check for missing parts after the first query
    missing_parts = check_missing_parts(
        original_query=original_query,
        expanded_query=query,
        agent_response=main_qa_pair[1],
        answered_parts=answered_parts,
        qa_pairs=qa_pairs
    )
    
    if missing_parts:
        info(f"Found {len(missing_parts)} missing parts, processing in parallel")
        # Add all missing parts to seen_queries to avoid duplicates
        for part in missing_parts:
            seen_queries.add(part)
        
        # Process missing parts in parallel
        new_qa_pairs = process_queries_in_parallel(agent, missing_parts, max_workers=max_parallel_workers)
        qa_pairs.extend(new_qa_pairs)
        
        # Add all processed parts to answered_parts
        for part, _ in new_qa_pairs:
            answered_parts.append(part)
            
        # Check if there are still missing parts after parallel processing
        remaining_iterations = max_retries - 2  # Account for first iteration and parallel batch
        iteration_count = 2  # Start with iteration 2
        
        # Continue with sequential processing for any remaining iterations if needed
        if remaining_iterations > 0:
            # Combine all responses into one text for comprehensive checking
            all_responses = "\n\n".join([resp for _, resp in qa_pairs])
            
            # Check for any remaining missing parts
            still_missing = check_missing_parts(
                original_query=original_query,
                expanded_query=query,
                agent_response=all_responses,
                answered_parts=answered_parts,
                qa_pairs=qa_pairs
            )
            
            # Process any remaining missing parts sequentially
            to_ask = [part for part in still_missing if part not in seen_queries]
            
            for iteration in range(remaining_iterations):
                iteration_count += 1
                if not to_ask:
                    info("No more questions to ask, ending agent loop")
                    break

                current_query = to_ask.pop(0)
                seen_queries.add(current_query)
                info(f"Iteration {iteration_count}: Asking agent: '{current_query}'")
                
                try:
                    # Invoke the agent with the current query
                    new_qa_pair = process_query(agent, current_query)
                    qa_pairs.append(new_qa_pair)
                    
                    # Consider this part answered even if some details are missing
                    answered_parts.append(current_query)
                    
                    # Only check for more missing parts if we have more iterations left
                    if iteration < remaining_iterations - 1 and to_ask:
                        all_responses = "\n\n".join([resp for _, resp in qa_pairs])
                        more_missing = check_missing_parts(
                            original_query=original_query,
                            expanded_query=query,
                            agent_response=all_responses,
                            answered_parts=answered_parts,
                            qa_pairs=qa_pairs
                        )
                        
                        # Add any new missing parts to the queue
                        for part in more_missing:
                            if part not in seen_queries:
                                info(f"Adding follow-up question: '{part}'")
                                to_ask.append(part)
                                seen_queries.add(part)
                                
                except Exception as e:
                    error(f"Error in agent iteration {iteration_count}: {str(e)}")
                    # Store the error as the response
                    qa_pairs.append((current_query, f"Error processing your request. {str(e)}"))
    
    info(f"Agent loop completed with {len(qa_pairs)} Q&A pairs")
    
    # Merge all responses into a cohesive answer
    final_response = merge_responses(original_query, query, qa_pairs, metadata)
    
    log_response(user_id, original_query, final_response)
    return final_response


