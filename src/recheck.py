from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

# GPT-4 to help check missing info
checker_llm = ChatOpenAI(model="gpt-4", temperature=0)
parser = StrOutputParser()

def check_missing_parts(original_query: str, agent_response: str) -> list[str]:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an assistant that identifies parts of a query that were NOT answered."),
        ("user", f"Original query: {original_query}\nAgent response: {agent_response}\n\nList the parts of the original query that were not answered. If everything is answered, say 'None'.")
    ])
    chain = prompt | checker_llm | parser
    missing_info = chain.invoke({})
    
    if "none" in missing_info.lower():
        return []
    return [line.strip("- ").strip() for line in missing_info.split("\n") if line.strip()]
