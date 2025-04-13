import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from src.tools.stock_info_tool import stock_tool
from src.tools.news_tool import news_tool 
from src.tools.company_analyzer_tool import company_analyzer_tool
from src.tools.fred_market_tool import fred_tool
from src.tools.stock_info_tool import financial_statements_tool
from src.tools.stock_info_tool import historical_performance_tool
from src.tools.stock_info_tool import technical_indicators_tool 
from src.tools.company_profile_tool import company_profile_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from src.prompts import (MISSING_INFO_CHECKER_PROMPT, RESPONSE_MERGER_PROMPT, 
                         QUERY_DECOMPOSITION_PROMPT, STOCK_TOOL_DESCRIPTION,
                         TABLE_AND_GRAPH_EXTRACTION_PROMPT)
from src.logger import info, error, log_request, log_response, warning, get_logger, log_agent_output
import uuid
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from langchain.tools import Tool

# Setup logger for the module
logger = get_logger("finance_flow")

# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Set up LangChain agent
llm = ChatOpenAI(temperature=0)

# Create a more explicit tool description for the stock tool
enhanced_stock_tool = Tool(
    name="Stock Info Tool",
    func=stock_tool.func,
    description=STOCK_TOOL_DESCRIPTION
)

agent = initialize_agent(
    tools=[enhanced_stock_tool, news_tool, company_analyzer_tool, fred_tool, company_profile_tool, financial_statements_tool, historical_performance_tool, technical_indicators_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# GPT-4 for advanced processing
gpt4_llm = ChatOpenAI(model="gpt-4-turbo", temperature=0)
parser = StrOutputParser()
json_parser = JsonOutputParser()

def decompose_query(original_query: str) -> List[Dict[str, Any]]:
    """
    Decompose a complex query into smaller, more focused sub-queries.
    
    This function analyzes the original query for multiple intents, entities,
    or requests and breaks it down into distinct sub-queries that can be
    processed independently.
    
    Args:
        original_query: The user's original query string
        
    Returns:
        A list of dictionaries, each containing:
        - 'sub_query': The text of the sub-query
        - 'focus': The main focus of this sub-query (e.g., 'stock_metrics', 'financials', 'news')
        - 'entities': Key entities (companies, tickers) relevant to this sub-query
        - 'priority': Priority score (1-10, with 10 being highest)
    """
    info(f"Decomposing complex query: '{original_query}'")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", QUERY_DECOMPOSITION_PROMPT)
    ])
    
    # Using JsonOutputParser to get structured output
    chain = prompt | gpt4_llm | json_parser
    
    try:
        # Parse the original query into sub-queries with metadata
        result = chain.invoke({"query": original_query})
        
        if not result or "sub_queries" not in result:
            # If decomposition fails, return the original as a single query
            info("Decomposition returned no sub-queries, using original query")
            fallback_result = [{
                "sub_query": original_query,
                "focus": "general",
                "entities": [],
                "priority": 10
            }]
            
            # Log the decomposition failure
            log_agent_output(
                agent_name="QueryDecomposition",
                input_text=original_query,
                output_text="Decomposition failed, using original query as fallback",
                metadata={"success": False}
            )
            
            return fallback_result
        
        sub_queries = result["sub_queries"]
        
        # Log the decomposition result
        info(f"Query decomposed into {len(sub_queries)} sub-queries:")
        for i, sq in enumerate(sub_queries):
            info(f"  Sub-query {i+1}: {sq['sub_query']} (focus: {sq['focus']}, priority: {sq['priority']})")
        
        # Sort sub-queries by priority (highest first)
        sorted_sub_queries = sorted(sub_queries, key=lambda x: x.get('priority', 0), reverse=True)
        
        # Log the successful decomposition
        log_agent_output(
            agent_name="QueryDecomposition",
            input_text=original_query,
            output_text=json.dumps(sorted_sub_queries, indent=2),
            metadata={"success": True, "num_sub_queries": len(sorted_sub_queries)}
        )
        
        return sorted_sub_queries
    
    except Exception as e:
        error(f"Error decomposing query: {str(e)}")
        # Return the original query as a fallback
        fallback_result = [{
            "sub_query": original_query,
            "focus": "general",
            "entities": [],
            "priority": 10
        }]
        
        # Log the decomposition error
        log_agent_output(
            agent_name="QueryDecomposition",
            input_text=original_query,
            output_text=f"Error: {str(e)}\nUsing original query as fallback",
            metadata={"success": False, "error": str(e)}
        )
        
        return fallback_result

def check_missing_parts(original_query: str, expanded_query: str, agent_response: str, answered_parts: list = None, qa_pairs: list = None) -> list[str]:
    """
    Check if parts of the query were not answered in the response
    
    Args:
        original_query: The user's original query
        expanded_query: Not used anymore, but kept for backward compatibility
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
        
        # Pre-process stock-related queries to help with company name to ticker conversion
        lower_query = query.lower()
        is_stock_query = any(term in lower_query for term in [
            "stock", "price", "share", "market cap", "p/e", "eps", "dividend", "ticker",
            "stock price", "shares", "valuation", "trading at", "worth"
        ])
        
        company_name_mapping = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "tesla": "TSLA",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "nvidia": "NVDA",
            "walmart": "WMT",
            "jpmorgan": "JPM",
            "jp morgan": "JPM",
            "bank of america": "BAC",
            "disney": "DIS",
            "coca cola": "KO",
            "coca-cola": "KO",
            "intel": "INTC",
            "amd": "AMD",
            "advanced micro devices": "AMD"
        }
        
        # For stock queries, add a hint to use the stock tool with the appropriate ticker
        if is_stock_query:
            for company, ticker in company_name_mapping.items():
                if company in lower_query:
                    # Modify the query to include the ticker for clarity
                    enhanced_query = f"{query} (Use the Stock Info Tool with ticker '{ticker}' to answer this query)"
                    info(f"Enhanced stock query with ticker info: '{enhanced_query}'")
                    query = enhanced_query
                    break
        
        # Execute the agent
        result = agent.invoke(query)
        response = result["output"] if isinstance(result, dict) else str(result)
        
        # Log the agent output for debugging
        log_agent_output(
            agent_name="LangChain",
            input_text=query,
            output_text=response,
            metadata={"is_stock_query": is_stock_query}
        )
        
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
    
    # Log the parallel processing results
    parallel_results_log = "\n".join([f"Query: {q}\nResponse: {r[:200]}..." for q, r in results])
    log_agent_output(
        agent_name="ParallelProcessing",
        input_text=str(queries),
        output_text=parallel_results_log,
        metadata={"num_queries": len(queries), "max_workers": max_workers}
    )
    
    return results

def merge_responses(original_query: str, expanded_query: str, qa_pairs: List, metadata: dict) -> str:
    """
    Merge multiple question-answer pairs into a coherent response.
    
    Args:
        original_query: The user's original query
        expanded_query: The expanded query after processing
        qa_pairs: List of question-answer tuples (question, answer)
        metadata: Additional metadata about the query processing
        
    Returns:
        A merged response that combines all the information from qa_pairs
    """
    # Log function entry
    info(f"Starting response merging process for query: '{original_query[:50]}...'")
    
    # Convert tuples to dictionaries if needed
    formatted_qa_pairs = []
    for pair in qa_pairs:
        if isinstance(pair, tuple) and len(pair) == 2:
            # Handle tuple format (question, answer)
            question, answer = pair
            formatted_qa_pairs.append({"question": question, "answer": answer})
        elif isinstance(pair, dict) and "question" in pair and "answer" in pair:
            # Handle dictionary format already
            formatted_qa_pairs.append(pair)
        else:
            warning(f"Skipping invalid QA pair format: {pair}")
    
    # Skip empty or non-response pairs
    valid_pairs = [pair for pair in formatted_qa_pairs 
                  if pair.get("answer") and 
                  not str(pair.get("answer")).lower().startswith("i don't know")]
    
    # Log detailed information about the valid and invalid pairs
    info(f"Merging {len(valid_pairs)} responses from {len(qa_pairs)} total pairs")
    info(f"Found {len(formatted_qa_pairs) - len(valid_pairs)} invalid/empty responses")
    
    # Log sample of input queries if available
    if valid_pairs:
        sample_questions = [f"'{pair.get('question', 'No question')[:50]}...'" for pair in valid_pairs[:3]]
        info(f"Sample input queries: {', '.join(sample_questions)}")
    
    # Log the QA pairs being merged
    log_agent_output(
        agent_name="ResponseMerger_Input",
        input_text=f"Original query: {original_query}\nExpanded query: {expanded_query}",
        output_text=json.dumps(valid_pairs, indent=2)[:1000] + "..." if len(json.dumps(valid_pairs, indent=2)) > 1000 else json.dumps(valid_pairs, indent=2),
        metadata={"num_total_pairs": len(qa_pairs), "num_valid_pairs": len(valid_pairs)}
    )
    
    if not valid_pairs:
        warning("No valid responses to merge")
        warning(f"Cannot proceed with merging - no valid responses for query: '{original_query}'")
        return "I don't have enough information to provide a comprehensive answer to your query about financial data."
    
    # Format the QA pairs for the prompt
    info("Formatting QA pairs for merger prompt")
    formatted_pairs = []
    for i, pair in enumerate(valid_pairs):
        formatted_pairs.append(f"Question {i+1}: {pair.get('question', '')}")
        formatted_pairs.append(f"Answer {i+1}: {pair.get('answer', '')}")
    
    qa_text = "\n\n".join(formatted_pairs)
    info(f"Created formatted QA text of length {len(qa_text)}")
    
    # Create prompt for merging responses
    info("Creating merger prompt and chain")
    prompt = ChatPromptTemplate.from_template(RESPONSE_MERGER_PROMPT)
    
    chain = prompt | gpt4_llm | parser
    
    try:
        info("Invoking response merger LLM chain")
        merged_response = chain.invoke({
            "original_query": original_query,
            "qa_pairs": qa_text
        })
        
        info(f"Generated merged response of length: {len(merged_response)}")
        info(f"Merged response first 100 chars: '{merged_response[:100]}...'")
        
        # Post-process to ensure no Q&A format remains
        info("Starting post-processing of merged response")
        final_response = post_process_response(merged_response, original_query)
        info(f"Post-processing complete, final response length: {len(final_response)}")
        
        # Log the final merged response
        log_agent_output(
            agent_name="ResponseMerger_Output",
            input_text="",
            output_text=final_response[:1000] + "..." if len(final_response) > 1000 else final_response,
            metadata={"success": True, "response_length": len(final_response)}
        )
        
        info("Response merging process completed successfully")
        return final_response
    except Exception as e:
        error_msg = str(e)
        error(f"Error merging responses: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {error_msg}")
        
        # Fallback to a simpler concatenation of answers
        info("Attempting fallback response generation")
        fallback_response = "Here's what I found:\n\n"
        for pair in valid_pairs:
            fallback_response += f"• {pair.get('answer', '')}\n\n"
        
        info(f"Generated fallback response of length {len(fallback_response)}")
        
        # Log the merger failure
        log_agent_output(
            agent_name="ResponseMerger_Fallback",
            input_text="",
            output_text=fallback_response[:1000] + "..." if len(fallback_response) > 1000 else fallback_response,
            metadata={"success": False, "error": error_msg, "exception_type": type(e).__name__}
        )
        
        return fallback_response

def post_process_response(response: str, original_query: str) -> str:
    """
    Post-process the response to ensure no question-answer format remains
    and to remove references to companies not in the original query
    
    Args:
        response: The merged response from the LLM
        original_query: The user's original query
        
    Returns:
        A processed response with no traces of Q&A format
    """
    # Check for Q&A pattern indicators
    qa_indicators = [
        "Q:", "Question:", "A:", "Answer:",
        "\nQ.", "\nQuestion.", "\nA.", "\nAnswer."
    ]
    
    has_qa_format = any(indicator in response for indicator in qa_indicators)
    
    # If Q&A format is detected, reprocess with a stronger prompt
    if has_qa_format:
        info("Q&A format detected in merged response, applying stricter reformatting")
        
        # Create a stronger prompt specifically for reformatting
        reformat_prompt = """
        You are a financial report editor. The text below contains information in a question-answer format,
        which is NOT acceptable for our final report. 
        
        Your task:
        1. Convert ALL question-answer pairs into flowing narrative paragraphs or tables
        2. COMPLETELY REMOVE any trace of the Q&A format
        3. Preserve ALL financial data and metrics
        4. Group related information together
        5. Use appropriate section headings
        
        Text to reformat:
        {text}
        
        Reformatted report (with NO question-answer format):
        """
        
        prompt = ChatPromptTemplate.from_template(reformat_prompt)
        reformat_chain = prompt | gpt4_llm | parser
        
        try:
            # Log the reformatting attempt
            log_agent_output(
                agent_name="ResponseReformatter_Input",
                input_text=response,
                output_text="",
                metadata={"has_qa_format": True}
            )
            
            reformatted_response = reformat_chain.invoke({"text": response})
            info("Successfully reformatted response to remove Q&A format")
            
            # Log the reformatting results
            log_agent_output(
                agent_name="ResponseReformatter_Output",
                input_text="",
                output_text=reformatted_response,
                metadata={"success": True}
            )
            
            response = reformatted_response
        except Exception as e:
            error(f"Error in post-processing: {str(e)}")
            
            # Manual fallback cleanup if LLM call fails
            for indicator in qa_indicators:
                response = response.replace(indicator, "")
            
            # Log the reformatting failure
            log_agent_output(
                agent_name="ResponseReformatter_Fallback",
                input_text="",
                output_text=f"Error: {str(e)}\nFalling back to manual replacement",
                metadata={"success": False, "error": str(e)}
            )
    
    # Additional check to ensure we're not presenting data about companies that weren't part of the original query
    # This prevents hallucinations where model discusses Microsoft when asked about Apple, etc.
    verification_prompt = """
    You are a financial data verification specialist. Review the financial report below and ensure it ONLY contains 
    information about the company or companies explicitly asked about in the original query.
    
    Original query: {original_query}
    
    Report to verify:
    {text}
    
    Your task:
    1. If the report contains data about companies NOT mentioned in the original query, remove those sections COMPLETELY
    2. If the report attributes data from one company (e.g., Apple) to another company (e.g., Microsoft), correct those attributions
    3. Make NO OTHER changes to the report content
    4. Return the corrected report with proper company attributions
    
    Corrected report:
    """
    
    try:
        # Log the verification input
        log_agent_output(
            agent_name="CompanyVerifier_Input",
            input_text=f"Query: {original_query}\n\nResponse to verify: {response[:500]}...",
            output_text="",
            metadata={}
        )
        
        verify_prompt = ChatPromptTemplate.from_template(verification_prompt)
        verify_chain = verify_prompt | gpt4_llm | parser
        
        verified_response = verify_chain.invoke({
            "original_query": original_query,
            "text": response
        })
        
        # Log the verification result
        log_agent_output(
            agent_name="CompanyVerifier_Output",
            input_text="",
            output_text=verified_response[:500] + "...",
            metadata={"success": True}
        )
        
        info("Successfully verified company references in response")
        return verified_response
    except Exception as e:
        error(f"Error in company verification: {str(e)}")
        
        # Log the verification failure
        log_agent_output(
            agent_name="CompanyVerifier_Error",
            input_text="",
            output_text=f"Error: {str(e)}\nReturning unverified response",
            metadata={"success": False, "error": str(e)}
        )
        
        return response

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
        Dictionary with the response text, sub-queries, QA pairs, and extracted visualizations
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
    
    # Decompose the query into sub-queries for more focused processing
    sub_queries = decompose_query(query)
    
    # If only one sub-query and it's the same as the original, proceed with the original flow
    if len(sub_queries) == 1 and sub_queries[0]["sub_query"] == query:
        # Original single-query processing flow
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
        
        # Extract tables and graphs from the response
        visualization_data = extract_visualizations(original_query, final_response)
        
        log_response(user_id, final_response)
        return {
            "query": original_query,
            "metadata": metadata or {},
            "response": final_response,
            "sub_queries": [sq["sub_query"] for sq in sub_queries],
            "qa_pairs": qa_pairs,
            "graphs": visualization_data.get("graphs", []),
            "tables": visualization_data.get("tables", [])
        }
    else:
        # Enhanced processing for decomposed queries
        info(f"Processing {len(sub_queries)} decomposed sub-queries")
        
        # Pre-process high-priority sub-queries in order to get core information first
        high_priority_queries = [sq["sub_query"] for sq in sub_queries if sq.get("priority", 0) >= 8]
        qa_pairs = []
        
        if high_priority_queries:
            info(f"Processing {len(high_priority_queries)} high-priority queries sequentially")
            for high_prio_query in high_priority_queries:
                qa_pair = process_query(agent, high_prio_query)
                qa_pairs.append(qa_pair)
        
        # Process remaining queries in parallel
        remaining_queries = [sq["sub_query"] for sq in sub_queries if sq.get("priority", 0) < 8]
        
        if remaining_queries:
            info(f"Processing {len(remaining_queries)} remaining queries in parallel")
            parallel_results = process_queries_in_parallel(
                agent, 
                remaining_queries, 
                max_workers=min(max_parallel_workers, len(remaining_queries))
            )
            qa_pairs.extend(parallel_results)
        
        # Final check for missing information from all collected responses
        all_responses = "\n\n".join([resp for _, resp in qa_pairs])
        
        still_missing = check_missing_parts(
            original_query=original_query,
            expanded_query=query,
            agent_response=all_responses,
            qa_pairs=qa_pairs
        )
        
        # Process any final missing parts if needed
        if still_missing:
            info(f"Processing {len(still_missing)} final missing parts")
            missing_results = process_queries_in_parallel(
                agent,
                still_missing,
                max_workers=min(max_parallel_workers, len(still_missing))
            )
            qa_pairs.extend(missing_results)
        
        # Merge all responses into a cohesive answer
        final_response = merge_responses(
            original_query=original_query,
            expanded_query=query,
            qa_pairs=qa_pairs,
            metadata=metadata or {}
        )
        
        # Extract tables and graphs from the response
        visualization_data = extract_visualizations(original_query, final_response)
        
        log_response(user_id, final_response)
        info(f"Agent loop completed for user {user_id}")
        
        return {
            "query": original_query,
            "metadata": metadata or {},
            "response": final_response,
            "sub_queries": [sq["sub_query"] for sq in sub_queries],
            "qa_pairs": qa_pairs,
            "graphs": visualization_data.get("graphs", []),
            "tables": visualization_data.get("tables", [])
        }

def extract_visualizations(query: str, response: str) -> dict:
    """
    Extract tables and graphs from the response data
    
    Args:
        query: Original user query for context
        response: Final response text to extract visualizations from
        
    Returns:
        Dictionary containing tables and graphs extracted from the response
    """
    info(f"Starting visualization extraction for response of length {len(response)}")
    
    # Create a prompt template
    prompt = ChatPromptTemplate.from_template(TABLE_AND_GRAPH_EXTRACTION_PROMPT)
    
    # Create a chain that will extract the visualizations
    chain = prompt | gpt4_llm | json_parser
    
    try:
        # Log the visualization extraction attempt
        log_agent_output(
            agent_name="VisualizationExtractor",
            input_text=f"Query: {query}\nResponse length: {len(response)}",
            output_text="",
            metadata={"response_preview": response[:200] + "..." if len(response) > 200 else response}
        )
        
        # Invoke the chain to extract visualizations
        extracted_data = chain.invoke({
            "query": query,
            "response": response
        })
        
        # Check if we got valid data
        if not isinstance(extracted_data, dict):
            info("Visualization extraction did not return a dictionary, defaulting to empty")
            extracted_data = {"tables": [], "graphs": []}
        
        # Ensure we have the expected keys
        tables = extracted_data.get("tables", [])
        graphs = extracted_data.get("graphs", [])
        
        info(f"Extracted {len(tables)} tables and {len(graphs)} graphs")
        
        # Log the successful extraction
        log_agent_output(
            agent_name="VisualizationExtractor_Result",
            input_text="",
            output_text=json.dumps(extracted_data, indent=2),
            metadata={"num_tables": len(tables), "num_graphs": len(graphs)}
        )
        
        return extracted_data
    except Exception as e:
        error_msg = str(e)
        error(f"Error extracting visualizations: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {error_msg}")
        
        # Return empty visualizations on error
        empty_result = {"tables": [], "graphs": []}
        
        # Log the extraction failure
        log_agent_output(
            agent_name="VisualizationExtractor_Error",
            input_text="",
            output_text=f"Error: {error_msg}",
            metadata={"success": False, "error": error_msg, "exception_type": type(e).__name__}
        )
        
        return empty_result


