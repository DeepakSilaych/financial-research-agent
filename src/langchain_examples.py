from langchain.agents import AgentType, initialize_agent, AgentExecutor, Tool
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from src.langchain_tools import FredMarketReportTool, CompanyAnalyzerTool

def simple_chain_example():
    """Example using the FRED tool in a simple LLM chain"""
    
    # Initialize the FRED market report tool
    fred_tool = FredMarketReportTool()
    
    # Create a prompt template
    template = """
    You are a financial analyst. Based on the following market data, provide a concise analysis:
    
    {market_data}
    
    Analysis:
    """
    
    prompt = PromptTemplate(
        input_variables=["market_data"],
        template=template,
    )
    
    # Create an LLM
    try:
        llm = ChatOpenAI(temperature=0)
        
        # Create the chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Get market data from FRED
        market_data = fred_tool.run({
            "indicators": ["GDP", "UNRATE", "CPIAUCSL"],
            "time_period": "1y"
        })
        
        # Run the chain
        response = chain.run(market_data=market_data)
        print("SIMPLE CHAIN EXAMPLE:")
        print(response)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Simple chain example requires OpenAI API key: {str(e)}")

def company_analysis_chain_example():
    """Example using the Company Analyzer tool in a simple LLM chain"""
    
    # Initialize the Company Analyzer tool
    company_tool = CompanyAnalyzerTool()
    
    # Create a prompt template
    template = """
    You are a stock market analyst specializing in technology companies. 
    Based on the following company data, provide a concise investment analysis and recommendation:
    
    {company_data}
    
    Investment Analysis and Recommendation:
    """
    
    prompt = PromptTemplate(
        input_variables=["company_data"],
        template=template,
    )
    
    # Create an LLM
    try:
        llm = ChatOpenAI(temperature=0)
        
        # Create the chain
        chain = LLMChain(llm=llm, prompt=prompt)
        
        # Get company data
        company_data = company_tool.run({
            "symbol": "AAPL"
        })
        
        # Run the chain
        response = chain.run(company_data=company_data)
        print("COMPANY ANALYSIS CHAIN EXAMPLE:")
        print(response)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Company analysis chain example requires OpenAI API key: {str(e)}")

def agent_example():
    """Example using the FRED tool with a LangChain agent"""
    
    # Initialize the FRED market report tool
    fred_tool = FredMarketReportTool()
    
    # Wrap the tool for the agent
    tools = [
        Tool(
            name="FRED_Market_Report",
            func=fred_tool.run,
            description=fred_tool.description
        )
    ]
    
    try:
        # Initialize the LLM
        llm = ChatOpenAI(temperature=0)
        
        # Initialize the agent
        agent = initialize_agent(
            tools, 
            llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        
        # Run the agent
        print("AGENT EXAMPLE:")
        response = agent.run(
            "Analyze current economic conditions focusing on inflation and unemployment. " 
            "Use a 6-month time period for analysis."
        )
        print(response)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Agent example requires OpenAI API key: {str(e)}")

def multi_tool_agent_example():
    """Example using both FRED and Company Analyzer tools with an agent"""
    
    # Initialize the tools
    fred_tool = FredMarketReportTool()
    company_tool = CompanyAnalyzerTool()
    
    # Wrap the tools for the agent
    tools = [
        Tool(
            name="FRED_Market_Report",
            func=fred_tool.run,
            description=fred_tool.description
        ),
        Tool(
            name="Company_Analyzer",
            func=company_tool.run,
            description=company_tool.description
        )
    ]
    
    try:
        # Initialize the LLM
        llm = ChatOpenAI(temperature=0)
        
        # Initialize the agent
        agent = initialize_agent(
            tools, 
            llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )
        
        # Run the agent
        print("MULTI-TOOL AGENT EXAMPLE:")
        response = agent.run(
            "First give me a summary of the current inflation environment using a 3-month time period. "
            "Then analyze Microsoft (MSFT) and tell me if the company's financial performance "
            "would make it a good hedge against the current economic conditions."
        )
        print(response)
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Multi-tool agent example requires OpenAI API key: {str(e)}")

def conversational_agent_example():
    """Example using the FRED tool with a conversational agent"""
    
    # Initialize the FRED market report tool
    fred_tool = FredMarketReportTool()
    company_tool = CompanyAnalyzerTool()
    
    # Wrap the tool for the agent
    tools = [
        Tool(
            name="FRED_Market_Report",
            func=fred_tool.run,
            description=fred_tool.description
        ),
        Tool(
            name="Company_Analyzer",
            func=company_tool.run,
            description=company_tool.description
        )
    ]
    
    try:
        # Initialize the LLM
        llm = ChatOpenAI(temperature=0)
        
        # Initialize conversation memory
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        
        # Initialize the agent
        agent = initialize_agent(
            tools, 
            llm, 
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory
        )
        
        # Run the agent with a conversation
        print("CONVERSATIONAL AGENT EXAMPLE:")
        
        # First query about economic data
        response1 = agent.run(
            "How has GDP been performing recently?"
        )
        print(f"Response 1: {response1}")
        
        # Second query about a company
        response2 = agent.run(
            "How is Apple performing financially?"
        )
        print(f"Response 2: {response2}")
        
        # Follow-up query that requires knowledge of both
        response3 = agent.run(
            "Given the economic conditions you described, is Apple well-positioned?"
        )
        print(f"Response 3: {response3}")
        
        print("\n" + "="*50 + "\n")
    except Exception as e:
        print(f"Conversational agent example requires OpenAI API key: {str(e)}")

if __name__ == "__main__":
    print("Financial Analysis Tools - Langchain Examples\n")
    
    # Run direct tool examples
    fred_tool = FredMarketReportTool()
    company_tool = CompanyAnalyzerTool()
    
    print("FRED MARKET REPORT TOOL - DIRECT USAGE:")
    fred_report = fred_tool.run({"indicators": ["UNRATE", "CPIAUCSL"], "time_period": "3m"})
    # Print first 300 characters as a sample
    print(f"{fred_report[:300]}...\n")
    print("="*50 + "\n")
    
    print("COMPANY ANALYZER TOOL - DIRECT USAGE:")
    try:
        company_report = company_tool.run({"symbol": "MSFT"})
        # Print first 300 characters as a sample
        print(f"{company_report[:300]}...\n")
    except Exception as e:
        print(f"Error: {str(e)}\n")
    print("="*50 + "\n")
    
    # Run examples that require OpenAI API
    simple_chain_example()
    company_analysis_chain_example()
    agent_example()
    multi_tool_agent_example()
    conversational_agent_example() 