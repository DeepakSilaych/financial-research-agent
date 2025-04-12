import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from tools.stock_info_tool import stock_tool 
from tools.news_tool import news_tool 
from tools.company_analyzer_tool import company_analyzer_tool
from tools.fred_market_tool import fred_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from prompts import MISSING_INFO_CHECKER_PROMPT
from logger import info, error, log_request, log_response
import uuid

# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Set up LangChain agent
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools=[stock_tool, news_tool, company_analyzer_tool, fred_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# GPT-4 to help check missing info
checker_llm = ChatOpenAI(model="gpt-4", temperature=0)
parser = StrOutputParser()

def check_missing_parts(original_query: str, agent_response: str) -> list[str]:
    """Check if parts of the original query were not answered in the response"""
    info(f"Checking for missing parts in response to: '{original_query}'")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", MISSING_INFO_CHECKER_PROMPT)
    ])
    chain = prompt | checker_llm | parser
    
    try:
        missing_info = chain.invoke({
            "original_query": original_query,
            "agent_response": agent_response
        })

        if "none" in missing_info.lower():
            info("No missing parts detected")
            return []
            
        missing_parts = [line.strip("- ").strip() for line in missing_info.split("\n") if line.strip()]
        info(f"Detected missing parts: {missing_parts}")
        return missing_parts
    except Exception as e:
        error(f"Error checking for missing parts: {str(e)}")
        return []

def run_agent_loop(agent, query, max_retries=3, user_id=None):
    """Run the agent with retry loop for handling missing information"""
    # Generate a session ID if not provided
    if not user_id:
        user_id = f"session_{uuid.uuid4().hex[:8]}"
        
    info(f"Starting agent loop for user {user_id} with query: '{query}'")
    log_request(user_id, query)
    
    seen_queries = set()
    to_ask = [query]
    final_response = ""
    iteration = 0

    for iteration in range(max_retries):
        if not to_ask:
            info("No more questions to ask, ending agent loop")
            break

        current_query = to_ask.pop(0)
        seen_queries.add(current_query)

        info(f"Iteration {iteration+1}: Asking agent: '{current_query}'")
        
        try:
            result = agent.invoke(current_query)
            response = result["output"] if isinstance(result, dict) else str(result)

            info(f"Agent response: {response[:100]}...")
            
            final_response += f"\nQ: {current_query}\nA: {response}\n"

            # Check what's missing
            missing = check_missing_parts(current_query, response)

            for part in missing:
                if part not in seen_queries:
                    info(f"Adding follow-up question: '{part}'")
                    to_ask.append(part)
        except Exception as e:
            error(f"Error in agent iteration {iteration+1}: {str(e)}")
            final_response += f"\nQ: {current_query}\nA: Error processing your request. {str(e)}\n"

    info(f"Agent loop completed after {iteration+1} iterations")
    log_response(user_id, query, final_response)
    return final_response
