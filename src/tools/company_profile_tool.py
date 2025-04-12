import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.tools import Tool
from pydantic import BaseModel, Field

# Load .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)
parser = StrOutputParser()

# Prompt
PROFILE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a financial analyst. Given a company name or ticker, give a detailed company profile including industry, business model, key products/services, market position, leadership, and recent news if available."),
    ("human", "{company_query}")
])

# Chain
company_chain = PROFILE_PROMPT | llm | parser

# Schema
class CompanyInput(BaseModel):
    company_query: str = Field(..., description="Name or ticker of a company, e.g., 'Tesla' or 'AAPL'")

# Tool
company_profile_tool = Tool(
    name="company_profile_tool",
    description="Use this to retrieve company overviews, products, industry, and latest info.",
    func=lambda company_query: company_chain.invoke({"company_query": company_query}),
    args_schema=CompanyInput
)

# ✅ Test block
if __name__ == "__main__":
    print("🏢 Testing Company Profile Tool...\n")
    
    test_queries = [
        "Apple",
        "Infosys",
        "TSLA",
        "What does Nvidia do?"
    ]
    
    for q in test_queries:
        print(f"\n🔎 Query: {q}")
        try:
            result = company_chain.invoke({"company_query": q})
            print(f"📄 Response:\n{result}")
        except Exception as e:
            print(f"❌ Error: {e}")
