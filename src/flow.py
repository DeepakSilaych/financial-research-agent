import os
from dotenv import load_dotenv
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from tool2 import stock_tool 
from tool3 import news_tool 

# Load .env file
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Set up LangChain agent
llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools=[stock_tool, news_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# === MAIN ===
if __name__ == "__main__":
    # Test with LangChain agent
    print("\n🤖 Agent test:")
    response = agent.invoke("What's the current price of TSLA?")
    print(response)
