import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from tool2 import stock_tool 
from tool3 import news_tool 
from tool4 import company_analyzer_tool
from tool5 import fred_tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# query = input("Enter your query: ")

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
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant that identifies parts of a query that were NOT answered."),
        ("user", "Original query: {original_query}\nAgent response: {agent_response}\n\nList the parts of the original query that were not answered. If everything is answered, say 'None'.")
    ])
    chain = prompt | checker_llm | parser
    missing_info = chain.invoke({
        "original_query": original_query,
        "agent_response": agent_response
    })

    if "none" in missing_info.lower():
        return []
    return [line.strip("- ").strip() for line in missing_info.split("\n") if line.strip()]



def run_agent_loop(agent, query, max_retries=3):
    seen_queries = set()
    to_ask = [query]
    final_response = ""

    for _ in range(max_retries):
        if not to_ask:
            break

        current_query = to_ask.pop(0)
        seen_queries.add(current_query)

        print(f"\n🤖 Asking: {current_query}")
        result = agent.invoke(current_query)
        response = result["output"] if isinstance(result, dict) else str(result)

        print(f"Agent Answer: {response}")
        final_response += f"\nQ: {current_query}\nA: {response}\n"

        # Check what’s missing
        missing = check_missing_parts(current_query, response)

        for part in missing:
            if part not in seen_queries:
                to_ask.append(part)

    return final_response
# run_agent_loop(agent, query, max_retries=3)


# === MAIN ===
if __name__ == "__main__":
    # Test with LangChain agent
    print("\n🤖 Agent test:")
    query = "What's the current price of TSLA?"

    run_agent_loop(agent, query, max_retries=3)
